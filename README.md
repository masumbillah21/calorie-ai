# CalorieAI

An AI-powered food calorie and nutrition tracker built with FastAPI, React, and a MobileNetV2-based food recognition model.

## Quick Start

### Linux / macOS
```bash
chmod +x setup.sh && ./setup.sh
```

### Windows
```text
Double-click setup.bat
```

### Manual
```bash
cp .env.example .env
docker compose up -d --build
```

Services:

- App: `http://localhost`
- API: `http://localhost/api`
- API docs: `http://localhost/api/docs`

## Project Structure

```text
calorie-ai/
|-- backend/
|   |-- Dockerfile
|   |-- main.py
|   |-- requirements.txt
|   `-- model/
|       |-- __init__.py
|       |-- class_names.json
|       |-- download_dataset.py
|       |-- predict.py
|       |-- train_model.py
|       `-- dataset/
|-- frontend/
|   |-- Dockerfile
|   |-- nginx.conf
|   |-- public/
|   `-- src/
|-- nginx/
|   `-- nginx.conf
|-- docker-compose.yml
|-- docker-compose.override.yml
|-- Makefile
|-- setup.bat
`-- setup.sh
```

## Model Training

The training assets now live under `backend/model/`.

```bash
# Download Food-101
make download-dataset

# Download + train
make setup-model

# Train only
make train

# Or run the trainer directly
cd backend/model && python train_model.py
```

Expected manual dataset path:

```text
backend/model/dataset/food-101/images/
```

Outputs:

- `backend/model/food_model.keras`
- `backend/model/class_names.json`

Dataset source:

- `https://www.kaggle.com/datasets/dansbecker/food-101`

After training, restart the backend:

```bash
make restart-api
```

## Makefile Commands

```bash
make start             # Build + start production
make dev               # Start with hot reload
make down              # Stop all services
make restart           # Restart all services
make restart-api       # Restart backend only
make build             # Rebuild images
make logs              # Stream all logs
make logs-api          # Backend logs only
make logs-ui           # Frontend logs only
make ps                # Container status
make shell-api         # Shell into backend container
make shell-ui          # Shell into frontend container
make install-train-deps
make download-dataset  # Download Food-101 into backend/model/dataset
make train             # Train the model locally
make setup-model       # Download dataset + train model
make clean             # Remove containers + volumes
make prune             # Full wipe
```

On Windows, `make install-train-deps` installs the training packages into your user Python site by default to avoid system-level permission conflicts.

## Tech Stack

- ML: TensorFlow 2.16.2, MobileNetV2
- Backend: FastAPI, Uvicorn, Python 3.11 (Docker) / 3.12-compatible local training
- Frontend: React 18, Vite, Recharts
- Containerization: Docker, Docker Compose
