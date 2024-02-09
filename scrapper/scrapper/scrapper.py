import os, asyncio, logging, uuid, httpx
from dotenv import dotenv_values
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from psycopg2 import OperationalError
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

async def fetch(url):
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=30)
        return response.text

async def parse_and_download_images(html, base_url, images_path):
    soup = BeautifulSoup(html, 'html.parser')
    catalog_divs = soup.find_all('div', class_='grid__catalog')

    tasks = []

    for catalog_div in catalog_divs:
        img_tags = catalog_div.find_all('img', class_='x-product-card__pic-img')
        for img_tag in img_tags:
            img_url = urljoin(base_url, img_tag['src'])
            tasks.append(download_image(img_url, images_path))

    await asyncio.gather(*tasks)

async def download_image(url, images_path):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=30)
            if response.status_code == 200:
                content_type = response.headers['Content-Type'].split('/')[-1]
                filename = str(uuid.uuid4()) + '.' + content_type
                save_path = os.path.join(images_path, filename)

                with open(save_path, 'wb') as f:
                    f.write(response.content)

                logger.info(f"Image saved: {filename}")
            else:
                logger.error(f"Failed to download image {url}: status code {response.status_code}")
    except httpx.ConnectError as e:
        logger.error(f"Connection error while downloading image {url}: {e}")

async def recreate_images_folder(images_path):
    if os.path.exists(images_path):
        for file in os.listdir(images_path):
            file_path = os.path.join(images_path, file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                logger.error(f"Error deleting file {file_path}: {e}")

        os.rmdir(images_path)

    os.mkdir(images_path)

async def main(start_url, max_images, images_path):
    await recreate_images_folder(images_path)

    page = 1
    images_downloaded = 0

    while images_downloaded < max_images:
        url = f"{start_url}page={page}"
        html = await fetch(url)
        await parse_and_download_images(html, start_url, images_path)
        page += 1

        # Подсчет количества загруженных изображений
        images_downloaded = len(os.listdir(images_path))

async def scrap(max_images, start_url):
    images_path = ENV["IMAGES_FOLDER"]
    await main(start_url, max_images, images_path)
