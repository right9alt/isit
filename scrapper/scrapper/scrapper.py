import asyncio, uuid, asyncpg, httpx, hashlib, os
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from scrapper import query
from fastapi import status

async def fetch(url, ctx):
  try:
    async with httpx.AsyncClient(timeout=int(os.getenv("TIMEOUT"))) as client:
      response = await client.get(url)
      return response.content
  except httpx.ReadTimeout:
    ctx.logger.error(f"Ошибка тайм-аута при получении {url}")

async def parse_and_save_images(catalog_divs, base_url, ctx):
  tasks = []

  for catalog_div in catalog_divs:
    img_tags = catalog_div.find_all('img', class_='x-product-card__pic-img')
    for img_tag in img_tags:
      img_url = urljoin(base_url, img_tag['src'])
      tasks.append(save_image(img_url, ctx))

  await asyncio.gather(*tasks)

async def save_image(url, ctx):
  try:
    async with httpx.AsyncClient() as client:
      response = await client.get(url, timeout=int(os.getenv("TIMEOUT")))
      if response.status_code == status.HTTP_200_OK:
        content_type = response.headers['Content-Type'].split('/')[-1]
        filename = str(uuid.uuid4()) + '.' + content_type
        file_content = response.content

        # Рассчитываем хэш содержимого файла
        file_hash = hashlib.sha256(file_content).hexdigest()

        async with ctx.db_handle.acquire() as conn:
          try:
            # Вставляем изображение в базу данных
            await query.insert_scrapped_image(conn, filename, file_hash, file_content)
            
            ctx.logger.info(f"Изображение сохранено: {filename}")
            return True  # Успешно вставлено в базу данных
          except asyncpg.exceptions.UniqueViolationError:
            ctx.logger.error(f"Изображение с хэшом {file_hash} уже существует, пропускаем...")
            return False  # Дубликат изображения, не вставляем
      else:
        ctx.logger.error(f"Не удалось загрузить изображение {url}: код состояния {response.status_code}")
        return False  # Не удалось загрузить изображение
  except httpx.ConnectError as e:
    ctx.logger.error(f"Ошибка соединения при загрузке изображения {url}: {e}")
    return False  # Ошибка соединения

async def main(start_url, max_images, ctx):
  images_saved = 0
  page = 1

  while images_saved < max_images:
    url = f"{start_url}page={page}"
    html = await fetch(url, ctx)
    soup = BeautifulSoup(html, 'html.parser')
    catalog_divs = soup.find_all('div', class_='grid__catalog')

    if not catalog_divs:
      ctx.logger.error(f"Не удалось загрузить {max_images}, недостаточно информации на сайте по данной ссылке")
      break

    tasks = []
    for catalog_div in catalog_divs:
      img_tags = catalog_div.find_all('img', class_='x-product-card__pic-img')
      for img_tag in img_tags:
        img_url = urljoin(start_url, img_tag['src'])
        tasks.append(save_image(img_url, ctx))

    results = await asyncio.gather(*tasks)
    page += 1
    # Подсчет успешно вставленных изображений
    images_saved += sum(results)
   
  ctx.logger.info(f"Сохранили требуемое количество изображений: {images_saved}")


async def scrap(max_images, start_url, ctx):
  await main(start_url, max_images, ctx)
