import cv2, asyncpg, logging
import numpy as np
from dotenv import dotenv_values

# Загрузка переменных окружения из файла .env
ENV = dotenv_values(".env")

# Настройка логгера
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создание обработчика файлов для записи логов в файл
file_handler = logging.FileHandler(ENV["PYRAMID_LOG"])
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

async def connect_database():
  try:
      conn = await asyncpg.connect(
          database = ENV["POSTGRES_DB"],
          user =     ENV["POSTGRES_USER"],
          password = ENV["POSTGRES_PASSWORD"],
          host =     ENV["POSTGRES_HOST"],
          port =     ENV["POSTGRES_PORT"]
      )

      await conn.execute("""
                  CREATE TABLE IF NOT EXISTS pyramid_images (
                      id SERIAL PRIMARY KEY,
                      file_name TEXT,
                      file_data BYTEA
                  )
              """)

      return conn
  except Exception as e:
      logger.error("Error connecting to database:", e)
      raise

async def fetch_image(conn, image_id):
  try:
      query = """
          SELECT file_data FROM selected_images WHERE id = $1
      """
      return await conn.fetchval(query, image_id)
  except Exception as e:
      logger.error(f"Error fetching image {image_id}:", e)
      raise

async def save_image(conn, file_name, file_data):
  try:
      query = """
          INSERT INTO pyramid_images (file_name, file_data) VALUES ($1, $2)
      """
      await conn.execute(query, file_name, file_data)
  except Exception as e:
      logger.error(f"Error saving image {file_name}:", e)
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

async def main(img1_id, img2_id):
  conn = await connect_database()
  
  param_sampling = 5

  img1_data = await fetch_image(conn, img1_id)
  img2_data = await fetch_image(conn, img2_id)

  # Преобразуем данные изображений в формат, пригодный для OpenCV
  img1 = cv2.imdecode(np.frombuffer(img1_data, np.uint8), cv2.IMREAD_COLOR)
  img2 = cv2.imdecode(np.frombuffer(img2_data, np.uint8), cv2.IMREAD_COLOR)

  img1 = cv2.resize(img1, (512, 512))
  img2 = cv2.resize(img2, (512, 512))

  gpA = await generate_gaussian_pyramid(img1, param_sampling)
  gpB = await generate_gaussian_pyramid(img2, param_sampling)

  lpA = await generate_laplacian_pyramid(gpA)
  lpB = await generate_laplacian_pyramid(gpB)

  LS = []
  for la, lb in zip(lpA, lpB):
      rows, cols, dpt = la.shape
      ls = np.hstack((la[:, :cols // 2], lb[:, cols // 2:]))
      LS.append(ls)

  ls_ = await reconstruct_image_from_pyramid(LS)

  # Сохраняем реконструированное изображение
  file_name = f"pyramid_{img1_id}_{img2_id}.jpg"
  success, encoded_image = cv2.imencode('.jpg', ls_)

  if success:
      await save_image(conn, file_name, encoded_image.tobytes())
  else:
      logger.error("Failed to encode the image.")

  await conn.close()

async def pyramid(img1_id, img2_id):
  await main(img1_id, img2_id)

