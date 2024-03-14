import torch, io, torchvision
from torchvision import transforms
from PIL import Image
from finder.utils import database

# Константы
MODEL_PATH = "bag_classifier.pth"  # Путь к файлу с предобученной моделью
CLASSES = ['bag', 'clutch', 'hobo', 'tout']  # Классы для классификации
MEAN = [0.485, 0.456, 0.406]  # Средние значения для нормализации
STD = [0.229, 0.224, 0.225]  # Стандартные отклонения для нормализации

# Функция для загрузки предобученной модели
def load_model(ctx):
    ctx.logger.info("Загрузка предобученной модели...")
    model = torchvision.models.resnet18(pretrained=False)
    num_ftrs = model.fc.in_features
    model.fc = torch.nn.Linear(num_ftrs, len(CLASSES))  # Изменение последнего слоя для соответствия количеству классов
    model.load_state_dict(torch.load(MODEL_PATH))
    model.eval()
    ctx.logger.info("Предобученная модель успешно загружена")
    return model

# Функция для загрузки и предобработки изображения из базы данных
async def load_image_from_database(ctx, target_image_id):
    try:
        ctx.logger.info("Получение изображения из базы данных...")
        async with ctx.db_handle.acquire() as conn:
            file_data = await database.fetch_row_selected_image(conn, target_image_id)
        if file_data:
            image = Image.open(io.BytesIO(file_data['file_data'])).convert('RGB')
            preprocess = transforms.Compose([
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(MEAN, STD)
            ])
            image_tensor = preprocess(image)
            image_tensor = image_tensor.unsqueeze(0)  # Добавление размерности пакета
            ctx.logger.info("Изображение успешно получено и предобработано")
            return image_tensor
        else:
            ctx.logger.error("Изображение не найдено в базе данных")
            return None
    except Exception as e:
        ctx.logger.error(f"Ошибка при получении изображения из базы данных: {e}")
        raise

async def predict_class(target_image_id, ctx):
    try:
        # Загрузка предобученной модели
        model = load_model(ctx)

        # Получение изображения из базы данных
        image_tensor = await load_image_from_database(ctx, target_image_id)

        if image_tensor is not None:
            # Предсказание класса
            with torch.no_grad():
                outputs = model(image_tensor)
                _, predicted = torch.max(outputs, 1)

            # Получение предсказанного класса
            predicted_class = predicted.item()
            predicted_label = CLASSES[predicted_class]

            ctx.logger.info("Предсказанный класс: %s", predicted_label)
            return predicted_label
        else:
            ctx.logger.error("Изображение не найдено в базе данных")
            return None
    except Exception as e:
        ctx.logger.error(f"Ошибка при выполнении классификации: {e}")
        raise
