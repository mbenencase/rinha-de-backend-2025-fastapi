build_image:
	docker build -f ./Dockerfile -t rinha-de-backend-2025-fastapi:latest .
	docker tag rinha-de-backend-2025-fastapi:latest mbenencase96/rinha-de-backend-2025-fastapi:latest
	docker push mbenencase96/rinha-de-backend-2025-fastapi:latest

dev:
	fastapi run app/main.py

up:
	docker compose -f ./docker-compose.yml up -d

down:
	docker compose -f ./docker-compose.yml down