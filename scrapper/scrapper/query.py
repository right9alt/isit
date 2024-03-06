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