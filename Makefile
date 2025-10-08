help:			
	@echo "==================================="
	@echo "  Django Project Makefile Commands "
	@echo "==================================="
	@awk -F':|##' ' \
		/^## / { \
			heading=substr($$0,4); \
			printf "\n\033[1;32m%s\033[0m\n", heading; \
		} \
		/^[a-zA-Z0-9_.-]+:.*##/ { \
			sub(/^[ \t]+/, "", $$1); \
			sub(/[ \t]+$$/, "", $$1); \
			sub(/^[ \t]+/, "", $$3); \
			sub(/[ \t]+$$/, "", $$3); \
			printf "  \033[36m%-20s\033[0m %s\n", $$1, $$3; \
		} \
	' $(MAKEFILE_LIST)


## Docker Commands
docker_prune: ## Prune unused Docker resources
	docker system prune -f


psql_up: ## Start timescale+postgrest 
	docker compose up --build -d


psql_down: ## Stop PostgreSQL container and remove volumes
	docker compose down -v


psql_terminal: ## Open a terminal in the PostgreSQL container
	docker exec -it timescale-db psql -U phisaver_user -d phisaver



## POSTGRESQL CLI
post_python: ## Run Python script to post data to PostgreSQL
	@echo "Running Python script to post data to PostgreSQL..."
	uv run Iotawatt_python/main.py

show_db: ## Display IoTaWatt data from PostgreSQL database
	@echo "Displaying IoTaWatt data from PostgreSQL database..."
	uv run show_db.py

generate_jwt: ## Generate JWT token for PostgREST API (phisaver role, 24h expiration)
	@echo "Generating JWT token for PostgREST API..."
	uv run generate_jwt.py generate phisaver --no-expiry

jwt_help: ## Show JWT generator help and available commands
	@echo "JWT Token Generator Help..."
	uv run generate_jwt.py

insert_fake: ## Insert fake IoTaWatt data for testing
	@echo "Inserting fake IoTaWatt data..."
	uv run Iotawatt_python/insert_fake_data.py


