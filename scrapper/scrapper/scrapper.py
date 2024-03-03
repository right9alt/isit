import os, asyncio, logging, uuid, httpx, asyncpg, hashlib
from dotenv import dotenv_values
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Настройка логгера
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения из файла .env
ENV = dotenv_values(".env")

# Создание обработчика для записи в файл
file_handler = logging.FileHandler(ENV["SCRAPPER_LOG"])
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

async def connect_database():
    try:
        # Создание пула соединений к базе данных "scrapper"
        pool = await asyncpg.create_pool(
            database=ENV["POSTGRES_DB"],
            user=ENV["POSTGRES_USER"],
            password=ENV["POSTGRES_PASSWORD"],
            host=ENV["POSTGRES_HOST"],
            port=ENV["POSTGRES_PORT"]
        )

        # Создание таблицы 'scrapped_images', если она не существует
        async with pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS scrapped_images (
                    id SERIAL PRIMARY KEY,
                    file_name TEXT,
                    file_hash TEXT UNIQUE,
                    file_data BYTEA
                )
            """)
        
        return pool
        
    except asyncpg.exceptions.PostgresError as e:
        logger.error(f"Error: {e}")

async def fetch(url):
    try:
        async with httpx.AsyncClient(timeout=60) as client:  # Увеличиваем таймаут до 60 секунд
            response = await client.get(url)
            return response.content
    except httpx.ReadTimeout:
        logger.error(f"Timeout error while fetching {url}")

async def parse_and_save_images(catalog_divs, base_url, pool):
    tasks = []

    for catalog_div in catalog_divs:
        img_tags = catalog_div.find_all('img', class_='x-product-card__pic-img')
        for img_tag in img_tags:
            img_url = urljoin(base_url, img_tag['src'])
            tasks.append(save_image(img_url, pool))

    await asyncio.gather(*tasks)

async def save_image(url, pool):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=30)
            if response.status_code == 200:
                content_type = response.headers['Content-Type'].split('/')[-1]
                filename = str(uuid.uuid4()) + '.' + content_type
                file_content = response.content

                # Calculate hash of the file content
                file_hash = hashlib.sha256(file_content).hexdigest()

                async with pool.acquire() as conn:
                    try:
                        # Insert image into the database
                        await conn.execute("""
                            INSERT INTO scrapped_images (file_name, file_hash, file_data)
                            VALUES ($1, $2, $3)
                        """, filename, file_hash, file_content)
                        
                        logger.info(f"Image saved: {filename}")
                    except asyncpg.exceptions.UniqueViolationError:
                        logger.error(f"Image with hash {file_hash} already exists, skipping...")
            else:
                logger.error(f"Failed to download image {url}: status code {response.status_code}")
    except httpx.ConnectError as e:
        logger.error(f"Connection error while downloading image {url}: {e}")

async def main(start_url, max_images, pool):
    page = 1
    images_saved = 0

    async with pool.acquire() as conn:
        images_before_start = await conn.fetchval("SELECT COUNT(*) FROM scrapped_images")

    while images_saved - images_before_start < max_images:
        url = f"{start_url}page={page}"
        html = await fetch(url)
        soup = BeautifulSoup(html, 'html.parser')
        catalog_divs = soup.find_all('div', class_='grid__catalog')

        if not catalog_divs:
            logger.error(f"Failed to download {max_images}, is not enough information on the site at the link")
            break

        await parse_and_save_images(catalog_divs, start_url, pool)
        page += 1

        # Count the number of saved images
        async with pool.acquire() as conn:
            images_saved = await conn.fetchval("SELECT COUNT(*) FROM scrapped_images")

async def scrap(max_images, start_url):
    pool = await connect_database()
    await main(start_url, max_images, pool)