import asyncio, asyncpg, logging, io
from rembg import remove
from PIL import Image
from modificator.utils import database

async def process_image(ctx, row):
  file_data = row["file_data"]
  file_name = row["file_name"]
  file_hash = row["file_hash"]
  
  # Удаление фона
  try:
    processed_data = await remove_background(file_data)
  except Exception as e:
    ctx.logger.error(f"Не удалось удалить фон из {file_name}: {e}")
    return

  # Сохранение обработанного изображения в новой таблице selected_images
  ctx.logger.info(f"Обработка изображения: {file_name}")
  async with ctx.db_handle.acquire() as conn:
    async with conn.transaction():
      try:
        await database.insert_selected_image(conn, file_name, file_hash, processed_data)
        ctx.logger.info(f"Фон удален для {file_name}")
      except asyncpg.exceptions.UniqueViolationError:
        ctx.logger.error(f"Обнаружен дубликат хэша файла для {file_name}, пропуск...")
      except Exception as e:
        ctx.logger.error(f"Не удалось вставить данные для {file_name}: {e}")

async def remove_background(file_data):
  # Преобразование байтов в объект PIL Image
  image = Image.open(io.BytesIO(file_data))
  # Удаление фона
  processed_image = await asyncio.to_thread(remove, image)
  # Преобразование обработанного изображения в байты
  processed_data = image_to_bytes(processed_image)
  return processed_data

def image_to_bytes(image):
  with io.BytesIO() as buffer:
    image.save(buffer, format='PNG')
    return buffer.getvalue()

async def process_images(ctx):
  async with ctx.db_handle.acquire() as conn:
    async with conn.transaction():
      scrapped_images = await database.fetch_all_scrapped_images_images(conn)
      for row in scrapped_images:
        try:
          async with conn.transaction():
            await process_image(ctx, row)
        except asyncpg.exceptions.UniqueViolationError:
          ctx.logger.error(f"Обнаружен дубликат хэша файла для {row['file_name']}, пропуск...")
        except Exception as e:
          ctx.logger.error(f"Ошибка при обработке изображения {row['file_name']}: {e}")


async def main(ctx):
  # Подключение к базе данных
  ctx.logger.info(f"Начат процесс удаления фона")

  # Выполнение обработки изображений асинхронно
  await process_images(ctx)

  ctx.logger.info(f"Процесс удаления фона завершен")

async def rem_bg(ctx):
  await main(ctx)
