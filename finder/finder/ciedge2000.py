import tqdm, cv2
from finder.utils import database
import numpy as np
from skimage.color import deltaE_ciede2000

async def fetch_image_data(ctx, image_id):
    # Получение данных изображения из базы данных по его ID.
    try:
        ctx.logger.info(f"Выполняется запрос данных изображения для ID {image_id}")
        async with ctx.db_handle.acquire() as conn:
            result = await database.fetch_row_selected_image(conn, image_id)
        if result is None:
            ctx.logger.warning(f"Данные изображения не найдены для ID {image_id}")
        else:
            ctx.logger.info(f"Данные изображения успешно загружены для ID {image_id}")
        return result
    except Exception as e:
        ctx.logger.error(f"Ошибка при запросе данных изображения для ID {image_id}: {e}")
        return None

def resize_image(image, target_size=(256, 256)):
    # Изменение размера изображения до указанного размера.
    return cv2.resize(image, target_size)

def bgra_2_lab(image_data, ctx):
    # Преобразование изображения из цветового пространства BGRA в CIELAB.
    try:
        image_array = np.frombuffer(image_data, dtype=np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_UNCHANGED)
        image_resized = resize_image(image)
        lab_img = cv2.cvtColor(image_resized, cv2.COLOR_BGR2Lab)
        return lab_img.astype(np.float32)
    except Exception as e:
        ctx.logger.error(f"Ошибка при преобразовании изображения в цветовое пространство Lab: {e}")
        return None

def histogram_mask(image, ctx):
    # Вычисление маски гистограммы изображения.
    try:
        hist_a = cv2.calcHist([image], [1], None, [32], [0, 256])
        hist_a = cv2.normalize(hist_a, hist_a).flatten()
        hist_b = cv2.calcHist([image], [2], None, [32], [0, 256])
        hist_b = cv2.normalize(hist_b, hist_b).flatten()
        return np.concatenate([hist_a, hist_b])
    except Exception as e:
        ctx.logger.error(f"Ошибка при вычислении маски гистограммы изображения: {e}")
        return None

def f1_score(precision, recall):
    # Вычисление F1-меры.
    try:
        return 2 * (precision * recall) / (precision + recall) if precision + recall != 0 else 0
    except ZeroDivisionError:
        return 0

async def get_top_similar_imgs(main_image_id, ctx, top_count=3):
    # Получение топовых похожих изображений по заданному ID основного изображения.
    top_similars = {}
    main_image_data = await fetch_image_data(ctx, main_image_id)
    if main_image_data is None:
        ctx.logger.warning(f"Данные изображения не найдены для ID {main_image_id}")
        return []

    im1_lab = bgra_2_lab(main_image_data['file_data'], ctx)
    if im1_lab is None:
        ctx.logger.warning(f"Ошибка при обработке изображения для ID {main_image_id}")
        return []

    im1_hist = histogram_mask(im1_lab, ctx)
    if im1_hist is None:
        ctx.logger.warning(f"Ошибка при вычислении маски гистограммы для изображения ID {main_image_id}")
        return []

    async with ctx.db_handle.acquire() as conn:
        async with conn.transaction():
            selected_images = await database.fetch_all_rows_without_target(conn, main_image_id)
            for row in selected_images:

                image_data = row['file_data']
                if image_data is None:
                    ctx.logger.warning(f"Данные изображения не найдены для ID {row['id']}")
                    continue

                im2_lab = bgra_2_lab(image_data, ctx)
                if im2_lab is None:
                    ctx.logger.warning(f"Ошибка при обработке изображения для ID {row['id']}")
                    continue

                similarity_lab = deltaE_ciede2000(im1_lab, im2_lab).mean()
                im2_hist = histogram_mask(im2_lab, ctx)
                if im2_hist is None:
                    ctx.logger.warning(f"Ошибка при вычислении маски гистограммы для изображения ID {row['id']}")
                    continue

                similarity_hist = cv2.compareHist(im1_hist, im2_hist, cv2.HISTCMP_INTERSECT)
                similarity = f1_score(similarity_lab, similarity_hist)
                top_similars[row['id']] = similarity

    if not top_similars:
        ctx.logger.warning("Похожие изображения не найдены.")
        return ['Похожие изображения не найдены.']

    top_similars = list(sorted(top_similars.items(), key=lambda item: item[1], reverse=True))
    top_image_ids = [top_item[0] for top_item in top_similars[:top_count]]
    return top_image_ids

async def ciedge2000(target_image_id, ctx):
    # Основная функция для поиска похожих изображений для заданного ID целевого изображения.
    try:
        similar_images = await get_top_similar_imgs(target_image_id, ctx)
        return similar_images
    except Exception as e:
        ctx.logger.error(f"Ошибка в основной функции: {e}")
        return []
