import torch
import torchvision
from torchvision import transforms
from PIL import Image
import asyncpg
import logging
from dotenv import dotenv_values
import io

# Константы
MODEL_PATH = "bag_classifier.pth"  # Путь к файлу с предобученной моделью
CLASSES = ['bag', 'clutch', 'hobo', 'tout']  # Классы для классификации
MEAN = [0.485, 0.456, 0.406]  # Средние значения для нормализации
STD = [0.229, 0.224, 0.225]  # Стандартные отклонения для нормализации

# Настройка логгера
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения из файла .env
ENV = dotenv_values(".env")

# Добавление обработчика файлов для записи логов в файл
file_handler = logging.FileHandler(ENV["HSV_LOG"])
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Подключение к базе данных PostgreSQL
async def connect_database():
    try:
        logger.info("Подключение к базе данных...")
        conn = await asyncpg.connect(
            database = ENV["POSTGRES_DB"],
            user     = ENV["POSTGRES_USER"],
            password = ENV["POSTGRES_PASSWORD"],
            host     = ENV["POSTGRES_HOST"],
            port     = ENV["POSTGRES_PORT"]
        )

        logger.info("Успешное подключение к базе данных")
        return conn
    except Exception as e:
        logger.error(f"Ошибка при подключении к базе данных: {e}")
        raise

# Функция для загрузки предобученной модели
def load_model(model_path, classes):
    logger.info("Загрузка предобученной модели...")
    model = torchvision.models.resnet18(pretrained=False)
    num_ftrs = model.fc.in_features
    model.fc = torch.nn.Linear(num_ftrs, len(classes))  # Изменение последнего слоя для соответствия количеству классов
    model.load_state_dict(torch.load(model_path))
    model.eval()
    logger.info("Предобученная модель успешно загружена")
    return model

# Функция для загрузки и предобработки изображения из базы данных
async def load_image_from_database(conn, target_image_id):
    try:
        logger.info("Получение изображения из базы данных...")
        query = "SELECT file_data FROM selected_images WHERE id = $1"
        file_data = await conn.fetchval(query, target_image_id)
        if file_data:
            image = Image.open(io.BytesIO(file_data)).convert('RGB')
            preprocess = transforms.Compose([
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(MEAN, STD)
            ])
            image_tensor = preprocess(image)
            image_tensor = image_tensor.unsqueeze(0)  # Добавление размерности пакета
            logger.info("Изображение успешно получено и предобработано")
            return image_tensor
        else:
            logger.error("Изображение не найдено в базе данных")
            return None
    except Exception as e:
        logger.error(f"Ошибка при получении изображения из базы данных: {e}")
        raise

async def main(target_image_id):
    try:
        # Загрузка предобученной модели
        model = load_model(MODEL_PATH, CLASSES)

        # Получение изображения из базы данных
        conn = await connect_database()
        image_tensor = await load_image_from_database(conn, target_image_id)

        if image_tensor is not None:
            # Предсказание класса
            with torch.no_grad():
                outputs = model(image_tensor)
                _, predicted = torch.max(outputs, 1)

            # Получение предсказанного класса
            predicted_class = predicted.item()
            predicted_label = CLASSES[predicted_class]

            logger.info("Предсказанный класс: %s", predicted_label)
            return predicted_label
        else:
            logger.error("Изображение не найдено в базе данных")
            return None
    except Exception as e:
        logger.error(f"Ошибка при выполнении классификации: {e}")
        raise

async def predict_class(target_image_id):
    return await main(target_image_id)
