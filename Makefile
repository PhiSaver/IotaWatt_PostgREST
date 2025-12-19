DOCKER = podman
COMPOSE =podman-compose
.SILENT:
.ONESHELL:
.PHONY: help images up down dbshell dbshell_reader logs post_python show_db jwt insert_fake veryclean

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'


images: ## Build Docker images
	$(COMPOSE) build postgrest-api
	$(COMPOSE) build timescale

up: down ## Start timescale+postgrest 
	$(COMPOSE) up -d

down: ## Stop PostgreSQL container 
	$(COMPOSE) down

dbshell: ## Open a terminal in the PostgreSQL container as admin
	$(DOCKER) exec -it timescale-db psql -U ${POSTGRES_USER} -d ${POSTGRES_DB}

dbshell_reader: ## Open a terminal in the PostgreSQL container
	$(DOCKER) exec -it timescale-db psql -U ${PG_READER_USER} -d ${POSTGRES_DB}

logs: ## View logs of all containers
	$(DOCKER) compose logs -f

show_db: ## Display IoTaWatt data from PostgreSQL database
	@echo "Displaying IoTaWatt data from PostgreSQL database..."
	uv run show_db.py

jwt: ## Generate JWT token for PostgREST API (writer, no expiry)
	uv run jwtutil.py generate writer --no-expiry


insert_fake: ## Insert fake IoTaWatt data for testing
	@echo "Inserting fake IoTaWatt data..."
	uv run Iotawatt_python/insert_fake_data.py


veryclean: ## Remove all volumes
	$(COMPOSE) down -v
	