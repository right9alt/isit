import torch, io, os
import torchvision.transforms as transforms
from finder.utils import database, constants
from PIL import Image
import numpy as np
from sklearn.neighbors import NearestNeighbors

async def get_embedding_from_db(ctx, image_id):
    try:
        async with ctx.db_handle.acquire() as conn:
            image_data = await database.fetch_row_selected_image(conn, image_id)
        with Image.open(io.BytesIO(image_data['file_data'])) as img:
            # Проверяем количество каналов изображения
            if img.mode == 'RGBA':
                img = img.convert('RGB')  # Преобразуем изображение в RGB, удаляя альфа-канал
            preprocess = transforms.Compose([
                transforms.Resize(constants.SIZE_256),
                transforms.CenterCrop(constants.SIZE_224),
                transforms.ToTensor(),
                transforms.Normalize(mean=constants.MEAN, std=constants.STD),
            ])
            image = preprocess(img)
            image = image.unsqueeze(0)
            with torch.no_grad():
                embedding = ctx.photo_model(image)
            return embedding.squeeze().numpy()
    except Exception as e:
        ctx.logger.error(f"Ошибка при получении эмбеддинга изображения: {e}")
        raise

async def search_similar_images(query_image_id, ctx, n_neighbors):
    try:
        # Создание объекта NearestNeighbors для поиска ближайших соседей
        knn = NearestNeighbors(n_neighbors, metric=os.getenv("PHOTO_METRI"))  # Используем косинусную метрику

        # Получаем эмбеддинг запроса изображения из базы данных
        query_embedding = await get_embedding_from_db(ctx, query_image_id)

        # Извлекаем все записи из базы данных для поиска соседей
        async with ctx.db_handle.acquire() as conn:
            async with conn.transaction():
                rows = await database.fetch_selected_images_ids(conn)
        ids = [row['id'] for row in rows]

        embeddings = []
        for image_id in ids:
            embedding = await get_embedding_from_db(ctx, image_id)
            embeddings.append(embedding)

        # Преобразование списка эмбеддингов в numpy массив
        embeddings = np.array(embeddings)

        # Обучение модели NearestNeighbors
        knn.fit(embeddings)

        # Поиск ближайших соседей для запроса изображения
        distances, indices = knn.kneighbors([query_embedding])

        # Возвращаем id из базы данных тех изображений, которые оказались самыми похожими на запрос
        return [ids[i] for i in indices[0]]
    except Exception as e:
        ctx.logger.error(f"Ошибка при поиске похожих изображений: {e}")
        raise

# Пример использования функции поиска и отображения похожих изображений
async def find_by_photo(target_image_id, ctx, n_neighbors):
    similar_image_ids = await search_similar_images(target_image_id, ctx, n_neighbors)
    return similar_image_ids
