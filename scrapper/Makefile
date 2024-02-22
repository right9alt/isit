include .env
export

setup:
	pip install --upgrade certifi
	curl -sSL https://install.python-poetry.org | python3 -
	cp .env.sample .env

recreate_images_folder:
	if [ ! -d "$(IMAGES_FOLDER)" ]; then \
			mkdir -p "$(IMAGES_FOLDER)"; \
			echo "Created directory: $(IMAGES_FOLDER)"; \
	fi

install:
	poetry install

runenv:
	poetry shell

execute: recreate_images_folder
	poetry run app
