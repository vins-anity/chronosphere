# Chronosphere

Chronosphere is a real-time Dota 2 game state ingestion and analysis platform. It processes live game data to predict win probabilities and provides a dashboard for visualization.

## Features

- **Real-time Ingestion**: Receives Game State Integration (GSI) data from Dota 2 clients.
- **Win Probability Prediction**: Uses an ML model (XGBoost) to predict win probability based on game state features.
- **Live Dashboard**: React/Vite frontend for visualizing game data and predictions in real-time.
- **Data Persistence**: Stores game ticks and match data in PostgreSQL.

## Tech Stack

- **Backend**: Python (FastAPI), SQLModel (ORM), Alembic (Migrations), AsyncPG.
- **Frontend**: React, Vite, Zustand, DaisyUI
- **Database**: PostgreSQL.
- **ML**: XGBoost, Scikit-learn.
- **Infrastructure**: Docker, Docker Compose.
- **Package Management**: `uv` (Python), `bun` (javascript)

## Setup

### Prerequisites

- Docker & Docker Compose
- Python 3.13+ (for local dev)
- `uv` (recommended for Python dependency management)

### Running with Docker (Recommended)

1.  Clone the repository.
2.  Create a `.env` file (copy from `.env.example` if available).
3.  Run the application:

    ```bash
    docker-compose up --build
    ```

4.  Access the services:
    - **Frontend**: http://localhost:3000
    - **Backend API Docs**: http://localhost:8000/docs

### Local Development

1.  **Backend**:
    ```bash
    # Install dependencies
    uv sync

    # Run database (if not using Docker for app)
    docker-compose up -d db

    # Run migrations
    uv run alembic upgrade head

    # Start server
    uv run uvicorn app.ingest.main:app --reload
    ```

2.  **Frontend**:
    ```bash
    cd frontend
    bun install
    bun dev
    ```

## Project Structure

- `app/`: Backend application code.
    - `core/`: Configuration, DB, WebSockets.
    - `ingest/`: API endpoints for GSI.
    - `ml/`: Machine learning models and feature extraction.
    - `worker/`: Background worker for processing data.
- `frontend/`: React frontend application.
- `alembic/`: Database migrations.
- `docker-compose.yml`: Service orchestration.

## License

[MIT](LICENSE)
