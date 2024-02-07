import os, asyncio, httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin

async def fetch(url):
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=30)  # установка времени ожидания ответа в секундах
        return response.text

async def parse_and_download_images(html, base_url, image_counter, images_path):
    soup = BeautifulSoup(html, 'html.parser')
    catalog_divs = soup.find_all('div', class_='grid__catalog')

    tasks = []

    for catalog_div in catalog_divs:
        img_tags = catalog_div.find_all('img', class_='x-product-card__pic-img')
        for img_tag in img_tags:
            img_url = urljoin(base_url, img_tag['src'])
            tasks.append(download_image(img_url, image_counter, images_path))  # передаем images_folder
            image_counter += 1

    await asyncio.gather(*tasks)
    return image_counter

async def download_image(url, image_counter, images_path):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=30)  # установка времени ожидания ответа в секундах
            if response.status_code == 200:
                content_type = response.headers['Content-Type'].split('/')[-1]
                filename = f"{image_counter}.{content_type}"
                save_path = os.path.join(images_path, filename)

                with open(save_path, 'wb') as f:
                    f.write(response.content)
                print(f"Image saved: {filename}")
    except httpx.ConnectError:
        print(f"Произошла ошибка подключения к серверу при загрузке изображения {url}. Пропускаем.")

async def recreate_images_folder(images_path):
    if os.path.exists(images_path):
        for file in os.listdir(images_path):
            file_path = os.path.join(images_path, file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(e)

        os.rmdir(images_path)

    os.mkdir(images_path)

async def main(start_url, max_images, images_path):
    await recreate_images_folder(images_path)

    image_counter = 1
    page = 1

    while image_counter <= max_images:
        url = f"{start_url}page={page}"
        html = await fetch(url)
        image_counter = await parse_and_download_images(html, start_url, image_counter, images_path)  # передаем images_folder
        page += 1

def start():
    start_url = "https://www.lamoda.ru/catalogsearch/result/?q=%D0%B6%D0%B5%D0%BD%D1%81%D0%BA%D0%BE%D0%B5+%D0%B1%D0%B5%D0%BB%D1%8C%D0%B5&submit=y&gender_section=women&"
    max_images = 1000  # установите количество изображений для загрузки
    images_folder = input("Введите путь до папки, где нужно создать папку 'images': ")
    images_path = os.path.join(images_folder, "images")
    asyncio.run(main(start_url, max_images, images_path))
