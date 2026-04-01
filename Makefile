MODEL_DIR := backend/model
TRAIN_PYTHON ?= python
TRAIN_PIP := $(TRAIN_PYTHON) -m pip

ifeq ($(OS),Windows_NT)
TRAIN_PIP_ARGS ?= --user
else
TRAIN_PIP_ARGS ?=
endif

.PHONY: build up start dev down restart restart-api logs logs-api logs-ui ps shell-api shell-ui env-setup install-train-deps download-dataset train setup-model clean prune help

build:
	docker compose -f docker-compose.yml build --no-cache

up:
	docker compose -f docker-compose.yml up -d
	@echo CalorieAI running!
	@echo   App: http://localhost
	@echo   API: http://localhost/api
	@echo   Docs: http://localhost/api/docs

start: build up

dev:
	docker compose up -d

down:
	docker compose down

restart:
	docker compose restart

restart-api:
	docker compose restart backend

logs:
	docker compose logs -f

logs-api:
	docker compose logs -f backend

logs-ui:
	docker compose logs -f frontend

ps:
	docker compose ps

shell-api:
	docker compose exec backend /bin/bash

shell-ui:
	docker compose exec frontend /bin/sh

env-setup:
	@if [ ! -f .env ]; then cp .env.example .env && echo ".env created"; else echo ".env already exists"; fi

install-train-deps:
	$(TRAIN_PIP) install $(TRAIN_PIP_ARGS) -r backend/requirements.txt matplotlib kagglehub

download-dataset: install-train-deps
	@echo Downloading Food-101 dataset...
	cd $(MODEL_DIR) && $(TRAIN_PYTHON) download_dataset.py

train: install-train-deps
	@echo Training food model...
	cd $(MODEL_DIR) && $(TRAIN_PYTHON) train_model.py

setup-model: download-dataset train
	@echo Model ready. Run 'make restart-api' to load the new weights.

clean:
	docker compose down -v

prune:
	docker compose down -v --rmi local

help:
	@echo CalorieAI Commands
	@echo   make start              Build + start production
	@echo   make dev                Start with hot reload
	@echo   make up                 Start cached images
	@echo   make down               Stop all
	@echo   make restart            Restart all
	@echo   make restart-api        Restart backend only
	@echo   make build              Rebuild images
	@echo   make logs               All logs
	@echo   make logs-api           Backend logs
	@echo   make logs-ui            Frontend logs
	@echo   make ps                 Container status
	@echo   make shell-api          Shell into backend
	@echo   make shell-ui           Shell into frontend
	@echo   make install-train-deps Install training dependencies
	@echo   make download-dataset   Download Food-101 into backend/model/dataset
	@echo   make train              Train the model locally
	@echo   make setup-model        Download dataset + train model
	@echo   make clean              Remove containers + volumes
	@echo   make prune              Full wipe
