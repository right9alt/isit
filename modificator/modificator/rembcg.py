import asyncio, asyncpg, logging, io
from rembg import remove
from PIL import Image
from dotenv import dotenv_values

# Загрузка переменных окружения из файла .env
ENV = dotenv_values(".env")

# Настройка логгера
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создание обработчика файлов для записи логов в файл
file_handler = logging.FileHandler(ENV["REMBCG_LOG"])
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

async def connect_database():
    try:
        # Создание пула подключений к базе данных
        pool = await asyncpg.create_pool(
            database = ENV["POSTGRES_DB"],
            user =     ENV["POSTGRES_USER"],
            password = ENV["POSTGRES_PASSWORD"],
            host =     ENV["POSTGRES_HOST"],
            port =     ENV["POSTGRES_PORT"]
        )

        # Создание таблицы "selected_images", если она не существует
        async with pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS selected_images (
                    id SERIAL PRIMARY KEY,
                    file_name TEXT,
                    file_hash TEXT UNIQUE,
                    file_data BYTEA
                )
            """)
        
        return pool
        
    except asyncpg.exceptions.PostgresError as e:
        logger.error(f"Ошибка: {e}")

async def process_image(conn, row):
    file_data = row["file_data"]
    file_name = row["file_name"]
    file_hash = row["file_hash"]
    
    # Удаление фона
    try:
        processed_data = await remove_background(file_data)
    except Exception as e:
        logger.error(f"Не удалось удалить фон из {file_name}: {e}")
        return

    # Сохранение обработанного изображения в новой таблице selected_images
    logger.info(f"Обработка изображения: {file_name}")
    async with conn.transaction():
        try:
            insert_query = """
                INSERT INTO selected_images (file_name, file_hash, file_data) 
                VALUES ($1, $2, $3)
            """
            await conn.execute(insert_query, file_name, file_hash, processed_data)
            logger.info(f"Фон удален для {file_name}")
        except asyncpg.exceptions.UniqueViolationError:
            logger.error(f"Обнаружен дубликат хэша файла для {file_name}, пропуск...")
        except Exception as e:
            logger.error(f"Не удалось вставить данные для {file_name}: {e}")

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

async def process_images(pool):
    async with pool.acquire() as conn:
        async with conn.transaction():
            async for row in conn.cursor("SELECT file_name, file_hash, file_data FROM scrapped_images"):
                try:
                    async with conn.transaction():
                        await process_image(conn, row)
                except asyncpg.exceptions.UniqueViolationError:
                    logger.error(f"Обнаружен дубликат хэша файла для {row['file_name']}, пропуск...")
                except Exception as e:
                    logger.error(f"Ошибка при обработке изображения {row['file_name']}: {e}")

async def main():
    # Подключение к базе данных
    pool = await connect_database()
    logger.info(f"Начат процесс удаления фона")

    # Выполнение обработки изображений асинхронно
    await process_images(pool)

    logger.info(f"Процесс удаления фона завершен")

    # Закрытие пула подключений к базе данных
    await pool.close()


async def rem_bg():
    await main()
