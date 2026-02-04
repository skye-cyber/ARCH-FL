# ARCH-FL Dashboard

A web-based interface for the ARCH-FL federated learning framework.

## 🚀 Quick Start

### Prerequisites
- Node.js (v16+)
- Python (v3.8+)
- SQLite (included with Python)

### Installation

```bash
# Install frontend dependencies
cd frontend
npm install
cd ..

# Install backend dependencies
pip install -r backend/requirements.txt
```

### Running the Dashboard

```bash
# Start backend (FastAPI)
cd backend
uvicorn main:app --reload

# In another terminal, start frontend
cd frontend
npm run dev
```

Access the dashboard at: `http://localhost:3000`

## 🏗️ Architecture

- **Frontend**: React + TypeScript + TailwindCSS
- **Backend**: FastAPI
- **Database**: SQLite

## 📦 Features

- Experiment configuration and management
- Real-time monitoring of federated learning
- Interactive architecture designer
- Results visualization and comparison
