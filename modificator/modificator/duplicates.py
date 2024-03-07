import io, imagehash, os, asyncio, asyncpg, logging
from PIL import Image
from modificator.utils import database

async def find_duplicate_and_unique_images(ctx, threshold=int(os.getenv("THRESHOLD"))):
  images = {}
  duplicates = []
  unique_images = []
  async with ctx.db_handle.acquire() as conn:
    async with conn.transaction():
      all_images = await database.fetch_all_scrapped_images_images(conn)
      for row in all_images:
        file_data = row["file_data"]
        with Image.open(io.BytesIO(file_data)) as img:
          img_hash = str(imagehash.phash(img))

        found_similar = False
        for key, val in images.items():
          if imagehash.hex_to_hash(img_hash) - imagehash.hex_to_hash(key) < threshold:
            duplicates.append((val, row["id"]))
            found_similar = True
            break

        if not found_similar:
          images[img_hash] = row["id"]
          unique_images.append(row["id"])

      async with ctx.db_handle.acquire() as conn:
        async with conn.transaction():
          for _, duplicate_id in duplicates:
            await database.delete_duplicate_image(conn, duplicate_id)
            ctx.logger.info(f"Удалено изображение-дубликат с id {duplicate_id}")

      return unique_images


async def main(ctx):

  ctx.logger.info(f"Поиск и удаление дубликатов - начало")

  # Поиск дубликатов и уникальных изображений
  await find_duplicate_and_unique_images(ctx)

  ctx.logger.info(f"Поиск и удаление дубликатов - завершено")

async def rem_dup(ctx):
  await main(ctx)
