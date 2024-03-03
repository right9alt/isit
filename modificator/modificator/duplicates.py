import io, imagehash, os, asyncio, asyncpg, logging
from PIL import Image
from dotenv import dotenv_values

# Загрузка переменных окружения из файла .env
ENV = dotenv_values(".env")

# Настройка логгера
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создание обработчика для записи в файл duplicates_log
file_handler = logging.FileHandler(ENV["DUPLICATES_LOG"])
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

async def connect_database():
    try:
        # Подключение к базе данных
        conn = await asyncpg.connect(
            database = ENV["POSTGRES_DB"],
            user     = ENV["POSTGRES_USER"],
            password = ENV["POSTGRES_PASSWORD"],
            host     = ENV["POSTGRES_HOST"],
            port     = ENV["POSTGRES_PORT"]
        )

        return conn

    except asyncpg.exceptions.PostgresError as e:
        logger.error(f"Error: {e}")

async def find_duplicate_and_unique_images(conn, threshold=5):
    images = {}
    duplicates = []
    unique_images = []

    async with conn.transaction():
        # Выборка всех изображений из таблицы scrapped_images
        async for row in conn.cursor("SELECT id, file_name, file_hash, file_data FROM scrapped_images"):
            file_data = row["file_data"]

            # Чтение изображения из данных в формате bytes
            with Image.open(io.BytesIO(file_data)) as img:
                img_hash = str(imagehash.phash(img))

            # Проверка наличия хеша в словаре хешей
            found_similar = False
            for key, val in images.items():
                if imagehash.hex_to_hash(img_hash) - imagehash.hex_to_hash(key) < threshold:
                    duplicates.append((val, row["id"]))
                    found_similar = True
                    break

            if not found_similar:
                images[img_hash] = row["id"]
                unique_images.append(row["id"])

    # Удаление дубликатов из таблицы scrapped_images
    async with conn.transaction():
        for _, duplicate_id in duplicates:
            await conn.execute("DELETE FROM scrapped_images WHERE id = $1", duplicate_id)
            logger.info(f"Deleted duplicate image with id {duplicate_id}")

    return unique_images

async def main():
    # Подключение к базе данных
    conn = await connect_database()
    logger.info(f"Find and remove duplicates - start")

    # Поиск дубликатов и уникальных изображений
    await find_duplicate_and_unique_images(conn)

    logger.info(f"Find and remove duplicates - end")

    # Закрытие соединения с базой данных
    await conn.close()

async def rem_dup():
    await main()
