build_image:
	docker build -f ./Dockerfile -t rinha-de-backend-2025-fastapi:latest .
	docker tag rinha-de-backend-2025-fastapi:latest mbenencase96/rinha-de-backend-2025-fastapi:latest
	docker push mbenencase96/rinha-de-backend-2025-fastapi:latest

dev:
	fastapi run app/main.py

make up:
	docker compose -f ./docker-compose.yml up -d
	docker compose -f ./payment-processor.yaml up -d

make down:
	docker compose -f ./docker-compose.yml down
	docker compose -f ./payment-processor.yaml down

up_api:
	docker compose -f ./docker-compose.yml up -d

down_api:
	docker compose -f ./docker-compose.yml down

test:
	k6 run rinha.js

up_payment:
	docker compose -f ./payment-processor.yaml up -d

down_payment:
	docker compose -f ./payment-processor.yaml down