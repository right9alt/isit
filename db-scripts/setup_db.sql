CREATE DATABASE isit;

\c isit;

CREATE TABLE IF NOT EXISTS public.scrapped_images (
    id SERIAL PRIMARY KEY,
    file_name TEXT,
    file_hash TEXT UNIQUE,
    file_data BYTEA
);