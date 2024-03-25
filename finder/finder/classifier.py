import torch, io, torchvision, os
from torchvision import transforms
from PIL import Image
from finder.utils import database, constants

# Функция для загрузки и предобработки изображения из базы данных
async def load_image_from_database(ctx, target_image_id):
    try:
        ctx.logger.info("Получение изображения из базы данных...")
        async with ctx.db_handle.acquire() as conn:
            file_data = await database.fetch_row_selected_image(conn, target_image_id)
        if file_data:
            image = Image.open(io.BytesIO(file_data['file_data'])).convert('RGB')
            preprocess = transforms.Compose([
                transforms.Resize((constants.SIZE_224, constants.SIZE_224)),
                transforms.ToTensor(),
                transforms.Normalize(constants.MEAN, constants.STD)
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
        model = ctx.classify_model

        # Получение изображения из базы данных
        image_tensor = await load_image_from_database(ctx, target_image_id)

        if image_tensor is not None:
            # Предсказание класса
            with torch.no_grad():
                outputs = model(image_tensor)
                _, predicted = torch.max(outputs, 1)

            # Получение предсказанного класса
            predicted_class = predicted.item()
            predicted_label = constants.CLASSES[predicted_class]

            ctx.logger.info("Предсказанный класс: %s", predicted_label)
            return predicted_label
        else:
            ctx.logger.error("Изображение не найдено в базе данных")
            return None
    except Exception as e:
        ctx.logger.error(f"Ошибка при выполнении классификации: {e}")
        raise
