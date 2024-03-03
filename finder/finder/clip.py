from dotenv import dotenv_values
import asyncpg, logging, io, torch
import clip
from PIL import Image

# Configure the logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from the .env file
ENV = dotenv_values(".env")

# Add a file handler to write logs to a file
file_handler = logging.FileHandler(ENV.get("CLIP_LOG"))
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

async def get_images(conn):
    try:
        query = f"SELECT id, file_data FROM selected_images"
        result = await conn.fetch(query)
        return result
    except Exception as e:
        logger.error(f"Ошибка при выполнении запроса к базе данных: {e}")
        raise

async def calculate_similarity(model, image, text):
    with torch.no_grad():
        image_features = model.encode_image(image)
        text_features = model.encode_text(text)
        similarity = (image_features @ text_features.T).cpu().numpy()
    return similarity[0][0]

async def text_search(model, preprocess, device, word, conn, save=5):
    text = clip.tokenize([word]).to(device)
    similarities = []

    images = await get_images(conn)

    for image_id, image_data in images:
        try:
            image_stream = io.BytesIO(image_data)
            image = preprocess(Image.open(image_stream)).unsqueeze(0).to(device)
            similarity = await calculate_similarity(model, image, text)
            similarities.append((image_id, similarity))
        except Exception as e:
            logger.error(f"Ошибка при обработке изображения {image_id}: {e}")

    similarities.sort(key=lambda x: x[1], reverse=True)

    return [image_id for image_id, _ in similarities[:save]]

def load_clip_model():
    logger.info('loading clip model...')
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, preprocess = clip.load("ViT-B/32", device=device)
    logger.info('clip loaded')
    return model, preprocess, device

async def clip_text_searcher(query, conn):
    model, preprocess, device = load_clip_model()

    return await text_search(model, preprocess, device, query, conn)

async def main(search_text):
    conn = await connect_database()

    image_ids = await clip_text_searcher(search_text, conn)

    logger.info(f"Found images with IDs: {image_ids}")

    await conn.close()

    return image_ids

async def clip_search(search_text):
    return await main(search_text)
