CREATE DATABASE isit;

\c isit;

CREATE TABLE IF NOT EXISTS scrapped_images (
    id SERIAL PRIMARY KEY,
    file_name TEXT,
    file_hash TEXT UNIQUE,
    file_data BYTEA
);

CREATE TABLE IF NOT EXISTS selected_images (
    id SERIAL PRIMARY KEY,
    scrapped_image_id INT UNIQUE,
    file_data BYTEA,
    FOREIGN KEY (scrapped_image_id) REFERENCES scrapped_images(id)
);

CREATE TABLE IF NOT EXISTS pyramid_images (
    id SERIAL PRIMARY KEY,
    file_data BYTEA,
    selected_image_id_1 INT,
    selected_image_id_2 INT,
    FOREIGN KEY (selected_image_id_1) REFERENCES selected_images(id),
    FOREIGN KEY (selected_image_id_2) REFERENCES selected_images(id)
);
