import asyncpg, torch, logging, io
import torchvision.transforms as transforms
from dotenv import dotenv_values
from torchvision.models import resnet50
from PIL import Image
import numpy as np
from sklearn.neighbors import NearestNeighbors

# Configure the logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from the .env file
ENV = dotenv_values(".env")

# Add a file handler to write logs to a file
file_handler = logging.FileHandler(ENV["PHOTO_LOG"])
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Подключение к базе данных PostgreSQL
async def connect_database():
    try:
        conn = await asyncpg.connect(
            database = ENV["POSTGRES_DB"],
            user     = ENV["POSTGRES_USER"],
            password = ENV["POSTGRES_PASSWORD"],
            host     = ENV["POSTGRES_HOST"],
            port     = ENV["POSTGRES_PORT"]
        )
        return conn
    except Exception as e:
        logger.error(f"Ошибка при подключении к базе данных: {e}")
        raise

# Загрузка предобученной модели ResNet50
model = resnet50(pretrained=True)
model = torch.nn.Sequential(*list(model.children())[:-1])
model.eval()

async def get_embedding_from_db(conn, image_id):
    try:
        query = "SELECT file_data FROM selected_images WHERE id = $1"
        image_data = await conn.fetchval(query, image_id)
        with Image.open(io.BytesIO(image_data)) as img:
            # Проверяем количество каналов изображения
            if img.mode == 'RGBA':
                img = img.convert('RGB')  # Преобразуем изображение в RGB, удаляя альфа-канал
            preprocess = transforms.Compose([
                transforms.Resize(256),
                transforms.CenterCrop(224),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ])
            image = preprocess(img)
            image = image.unsqueeze(0)
            with torch.no_grad():
                embedding = model(image)
            return embedding.squeeze().numpy()
    except Exception as e:
        logger.error(f"Ошибка при получении эмбеддинга изображения: {e}")
        raise


# Создание объекта NearestNeighbors для поиска ближайших соседей
knn = NearestNeighbors(n_neighbors=5, metric='cosine')  # Используем косинусную метрику

async def search_similar_images(query_image_id, knn, conn):
    try:
        # Получаем эмбеддинг запроса изображения из базы данных
        query_embedding = await get_embedding_from_db(conn, query_image_id)

        # Извлекаем все записи из базы данных для поиска соседей
        rows = await conn.fetch("SELECT id FROM selected_images")
        ids = [row['id'] for row in rows]

        embeddings = []
        for image_id in ids:
            embedding = await get_embedding_from_db(conn, image_id)
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
        logger.error(f"Ошибка при поиске похожих изображений: {e}")
        raise

# Пример использования функции поиска и отображения похожих изображений
async def main(target_image_id):
    conn = await connect_database()
    similar_image_ids = await search_similar_images(target_image_id, knn, conn)
    return similar_image_ids

async def find_by_photo(target_image_id):
    return await main(target_image_id)