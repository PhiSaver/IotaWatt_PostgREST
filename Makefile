DOCKER = podman
COMPOSE = podman-compose
SSH = ssh your-server.example.com
.SILENT:
.ONESHELL:
.PHONY: help images up down dbshell dbshell_reader logs jwt show_db upload_sample veryclean dist deploy-local deploy-remote

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) |  awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'


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

jwt: ## Generate JWT token for PostgREST API (writer, no expiry)
	uv run jwtutil.py generate writer --no-expiry

show_db: ## Display IoTaWatt data from PostgreSQL database
	@echo "Displaying IoTaWatt data from PostgreSQL database..."
	uv run show_db.py

test: ## Test PostgREST API connectivity	
	test.sh
	
clean:
	rm -rf dist/*

veryclean: ## Remove all volumes
	$(COMPOSE) down -v

dist: ## Create deployment package in dist/ directory
	mkdir -p dist/quadlets
	cp devops/quadlets/* dist/quadlets/
	cp devops/install.sh dist/
	cp .env dist/
	cp init_db.sh dist/
	chmod +x dist/install.sh

deploy-local: dist ## Deploy to local machine 
	mkdir -p $(DEPLOY_DIR)
	cp -r dist/* $(DEPLOY_DIR)/
	cp .env $(DEPLOY_DIR)/
	cd $(DEPLOY_DIR) && bash install.sh

deploy-remote: dist ## Deploy to remote host via ssh ($(SSH):$(DEPLOY_DIR))
	$(SSH) "mkdir -p $(DEPLOY_DIR)"
	rsync -avz --delete dist/ $(SSH):$(DEPLOY_DIR)/
	$(SSH) "cd $(DEPLOY_DIR) && bash install.sh"
	
	