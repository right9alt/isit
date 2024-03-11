import cv2, asyncpg, logging
import numpy as np
from modificator.utils import database 

async def fetch_image(ctx, image_id):
  try:
    async with ctx.db_handle.acquire() as conn:
      async with conn.transaction():
        image_data = await database.selected_image_by_id(conn, image_id)
        if image_data is None:
          ctx.logger.error(f"Изображение не найдено ID: {image_id}")
        else:
          ctx.logger.info(f"Изображение найдено с ID: {image_id}")
        return image_data
  except Exception as e:
    ctx.logger.error(f"Ошибка поиска изображения {image_id}: {e}")
    raise

async def save_image(ctx, file_data, img1_id, img2_id):
  try:
    await database.save_pyramid_image(ctx.db_handle, file_data, img1_id, img2_id)
  except Exception as e:
    ctx.logger.error(f"Ошибка при сохранении изображения pyramid_{img1_id}_{img2_id}:", e)
    raise

async def generate_gaussian_pyramid(image, levels):
  pyramid = [image.copy()]
  for _ in range(levels):
    image = cv2.pyrDown(image)
    pyramid.append(image)
  return pyramid

async def generate_laplacian_pyramid(gaussian_pyramid):
  laplacian_pyramid = [gaussian_pyramid[-1]]
  for i in range(len(gaussian_pyramid) - 1, 0, -1):
    expanded = cv2.pyrUp(gaussian_pyramid[i])
    laplacian = cv2.subtract(gaussian_pyramid[i - 1], expanded)
    laplacian_pyramid.append(laplacian)
  return laplacian_pyramid

async def reconstruct_image_from_pyramid(laplacian_pyramid):
  reconstructed_image = laplacian_pyramid[0]
  for i in range(1, len(laplacian_pyramid)):
    reconstructed_image = cv2.pyrUp(reconstructed_image)
    reconstructed_image = cv2.add(reconstructed_image, laplacian_pyramid[i])
  return reconstructed_image

async def pyramid_start(img1_id, img2_id, ctx):
  
  img1_data = await fetch_image(ctx, img1_id)
  img2_data = await fetch_image(ctx, img2_id)

  if img1_data is None or img2_data is None:
    ctx.logger.error("Не удалось загрузить данные изображения.")
    return

  # Преобразуем данные изображений в формат, пригодный для OpenCV
  img1 = cv2.imdecode(np.frombuffer(img1_data, np.uint8), cv2.IMREAD_COLOR)
  img2 = cv2.imdecode(np.frombuffer(img2_data, np.uint8), cv2.IMREAD_COLOR)

  img1 = cv2.resize(img1, (512, 512))
  img2 = cv2.resize(img2, (512, 512))

  paramid_samplings = 5

  gpA = await generate_gaussian_pyramid(img1, paramid_samplings)
  gpB = await generate_gaussian_pyramid(img2, paramid_samplings)

  lpA = await generate_laplacian_pyramid(gpA)
  lpB = await generate_laplacian_pyramid(gpB)

  LS = []
  for la, lb in zip(lpA, lpB):
    rows, cols, dpt = la.shape
    ls = np.hstack((la[:, :cols // 2], lb[:, cols // 2:]))
    LS.append(ls)

  ls_ = await reconstruct_image_from_pyramid(LS)

  # Сохраняем реконструированное изображение
  success, encoded_image = cv2.imencode('.jpg', ls_)

  if success:
    await save_image(ctx, encoded_image.tobytes(), img1_id, img2_id)
  else:
    ctx.logger.error("Не удалось закодировать изображение.")

