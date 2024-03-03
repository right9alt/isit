import cv2, asyncpg, logging
import numpy as np
from dotenv import dotenv_values
from typing import List, Tuple

# Configure the logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from the .env file
ENV = dotenv_values(".env")

# Add a file handler to write logs to a file
file_handler = logging.FileHandler(ENV["HSV_LOG"])
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

async def connect_database():
    logger.info("Connecting to the database...")
    conn = await asyncpg.connect(
        database = ENV["POSTGRES_DB"],
        user     = ENV["POSTGRES_USER"],
        password = ENV["POSTGRES_PASSWORD"],
        host     = ENV["POSTGRES_HOST"],
        port     = ENV["POSTGRES_PORT"]
    )
    logger.info("Successfully connected to the database")
    return conn

async def fetch_image_data(conn, image_id):
    logger.info(f"Fetching image data for ID: {image_id}")
    query = "SELECT id, file_data FROM selected_images WHERE id = $1"
    row = await conn.fetchrow(query, image_id)
    if row:
        logger.info(f"Image data fetched successfully for ID: {image_id}")
        return row['file_data']
    else:
        logger.warning(f"No image data found for ID: {image_id}")
        return None

def calculate_hist_hsv(image_data):
    logger.info("Calculating HSV histogram")
    image = cv2.imdecode(np.frombuffer(image_data, np.uint8), cv2.IMREAD_COLOR)
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    hist_hsv = cv2.calcHist([hsv_image], [0, 1, 2], None, [32, 32, 32], [0, 180, 0, 256, 0, 256])
    hist_hsv = cv2.normalize(hist_hsv, hist_hsv).flatten()
    logger.info("HSV histogram calculated successfully")
    return hist_hsv

async def find_similar_images_db(target_image_id, conn, top_n=3) -> List[Tuple[int, float]]:
    logger.info(f"Finding similar images for target image ID: {target_image_id}")
    target_image_data = await fetch_image_data(conn, target_image_id)
    if not target_image_data:
        raise ValueError(f"Image not found for ID: {target_image_id}")

    target_hist = calculate_hist_hsv(target_image_data)

    similarities = []

    async with conn.transaction():  # Start a transaction
        query = "SELECT id, file_data FROM selected_images WHERE id != $1"
        async for row in conn.cursor(query, target_image_id):
            image_id = row['id']
            image_data = row['file_data']
            hist = calculate_hist_hsv(image_data)
            similarity = cv2.compareHist(target_hist, hist, cv2.HISTCMP_BHATTACHARYYA)
            similarities.append((image_id, similarity))

    similarities.sort(key=lambda x: x[1])

    most_similar_images = similarities[:top_n]
    logger.info(f"Found {len(most_similar_images)} similar images")
    return most_similar_images

async def main(target_image_id):
    logger.info(f"Starting main function for target image ID: {target_image_id}")
    conn = await connect_database()

    try:
        similar_images_db = await find_similar_images_db(target_image_id, conn)
        await conn.close()
        return similar_images_db
    finally:
        logger.info("Closing database connection")
        await conn.close()

async def hsv(target_image_id):
    return await main(target_image_id)
