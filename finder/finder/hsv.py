import cv2
from finder.utils import database
import numpy as np
from typing import List, Tuple

async def fetch_image_data(ctx, image_id):
    ctx.logger.info(f"Поиск изображения по ID: {image_id}")
    async with ctx.db_handle.acquire() as conn:
        row = await database.fetch_row_selected_image(conn, image_id)
    if row:
        ctx.logger.info(f"Изображение успешно найдено по ID: {image_id}")
        return row['file_data']
    else:
        ctx.logger.warning(f"Изображение не найдено по ID: {image_id}")
        return None

def calculate_hist_hsv(image_data, ctx):
    ctx.logger.info("Считаем HSV гистограмму")
    image = cv2.imdecode(np.frombuffer(image_data, np.uint8), cv2.IMREAD_COLOR)
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    hist_hsv = cv2.calcHist([hsv_image], [0, 1, 2], None, [32, 32, 32], [0, 180, 0, 256, 0, 256])
    hist_hsv = cv2.normalize(hist_hsv, hist_hsv).flatten()
    ctx.logger.info("HSV гистограмма посчитана")
    return hist_hsv

async def find_similar_images_db(target_image_id, ctx, top_n=3) -> List[Tuple[int, float]]:
    ctx.logger.info(f"Поиск похожих по HSV для изображения с ID: {target_image_id}")
    target_image_data = await fetch_image_data(ctx, target_image_id)
    if not target_image_data:
        raise ValueError(f"Изображение не найдено по ID: {target_image_id}")

    target_hist = calculate_hist_hsv(target_image_data, ctx)

    similarities = []

    async with ctx.db_handle.acquire() as conn:
        async with conn.transaction():
            selected_images = await database.fetch_all_rows_without_target(conn, target_image_id)
            for row in selected_images:
                image_id = row['id']
                image_data = row['file_data']
                hist = calculate_hist_hsv(image_data, ctx)
                similarity = cv2.compareHist(target_hist, hist, cv2.HISTCMP_BHATTACHARYYA)
                similarities.append((image_id, similarity))

    similarities.sort(key=lambda x: x[1])

    most_similar_images = similarities[:top_n]
    ctx.logger.info(f"Найдено {len(most_similar_images)} похожие изобр-я")
    return most_similar_images

async def hsv(target_image_id, ctx):
    ctx.logger.info(f"Старт поиска для изображения с ID: {target_image_id}")

    similar_images_db = await find_similar_images_db(target_image_id, ctx)
    return similar_images_db


