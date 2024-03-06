setdata:
	cp .secrets/scrapper.env.sample .secrets/scrapper.env
	cp .secrets/postgres.env.sample .secrets/postgres.env

execute: setdata; docker-compose up
rebuild: setdata; docker-compose up --build
clean:   ; docker-compose down --rmi all -v --remove-orphans