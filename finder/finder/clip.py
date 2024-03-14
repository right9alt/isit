from dotenv import dotenv_values
import io, torch
from finder.utils import database
import clip
from PIL import Image

async def get_images(ctx):
    try:
        async with ctx.db_handle.acquire() as conn:
            async with conn.transaction():
                result = await database.fetch_all_selected_images_id_data(conn)
                return result
    except Exception as e:
        ctx.logger.error(f"Ошибка при выполнении запроса к базе данных: {e}")
        raise

async def calculate_similarity(model, image, text):
    with torch.no_grad():
        image_features = model.encode_image(image)
        text_features = model.encode_text(text)
        similarity = (image_features @ text_features.T).cpu().numpy()
    return similarity[0][0]

async def text_search(model, preprocess, device, word, ctx, save=5):
    text = clip.tokenize([word]).to(device)
    similarities = []

    images = await get_images(ctx)

    for image_id, image_data in images:
        try:
            image_stream = io.BytesIO(image_data)
            image = preprocess(Image.open(image_stream)).unsqueeze(0).to(device)
            similarity = await calculate_similarity(model, image, text)
            similarities.append((image_id, similarity))
        except Exception as e:
            ctx.logger.error(f"Ошибка при обработке изображения {image_id}: {e}")

    similarities.sort(key=lambda x: x[1], reverse=True)

    return [image_id for image_id, _ in similarities[:save]]

def load_clip_model(ctx):
    ctx.logger.info('загрузка clip модели...')
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, preprocess = clip.load("ViT-B/32", device=device)
    ctx.logger.info('clip загружена')
    return model, preprocess, device

async def clip_text_searcher(query, ctx):
    model, preprocess, device = load_clip_model(ctx)

    return await text_search(model, preprocess, device, query, ctx)

async def clip_search(search_text, ctx):

    image_ids = await clip_text_searcher(search_text, ctx)

    ctx.logger.info(f"Поиск изображений с IDs: {image_ids}")

    return image_ids
