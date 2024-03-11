import asyncpg, os

async def connect():
  try:
    # Создание пула соединений к базе данных
    pool = await asyncpg.create_pool(os.getenv("DATABASE_URL"))
      
  except Exception as e:
    # Обработка ошибок подключения к базе данных
    raise ConnectionError(f"Ошибка подключения к базе данных: {e}")
  
  return pool

async def disconnect(conn):
    """Закрываем соединение с базой данных."""
    await conn.close()

async def insert_scrapped_image(conn, filename, file_hash, file_content):
  """Вставить информацию о скрапленном изображении в базу данных."""
  await conn.execute("""
      INSERT INTO public.scrapped_images (file_name, file_hash, file_data)
      VALUES ($1, $2, $3)
  """, filename, file_hash, file_content)

async def fetch_all_scrapped_images_images(conn):
  async with conn.transaction():
    return await conn.fetch("SELECT id, file_name, file_hash, file_data FROM scrapped_images")

async def delete_duplicate_image(conn, duplicate_id):
  await conn.execute("DELETE FROM scrapped_images WHERE id = $1", duplicate_id)

async def save_pyramid_image(conn, file_data, selected_image_id_1, selected_image_id_2):
  insert_query = "INSERT INTO pyramid_images ( file_data, selected_image_id_1, selected_image_id_2) VALUES ($1, $2, $3)"
  await conn.execute(insert_query, file_data, selected_image_id_1, selected_image_id_2)

async def selected_image_by_id(conn, image_id):
  async with conn.transaction():
    return await conn.fetchval("SELECT file_data FROM selected_images WHERE id = $1", image_id)

async def insert_selected_image(conn, fk_scrapped_image_id, processed_data):
  insert_query = """
    INSERT INTO selected_images (scrapped_image_id, file_data)
    VALUES ($1, $2)
  """
  await conn.execute(insert_query, fk_scrapped_image_id, processed_data)