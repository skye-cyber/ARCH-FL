"""
ARCH-FL Dashboard Backend - FastAPI Application

Main application entry point with API endpoints for the dashboard.
"""

from fastapi.responses import HTMLResponse
from fastapi import WebSocket, WebSocketDisconnect
import os
import sys
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import sqlite3
import json

# Add project root to path for ARCH-FL core integration
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

# Initialize FastAPI app
app = FastAPI(
    title="ARCH-FL Dashboard API",
    description="Backend API for ARCH-FL Federated Learning Dashboard",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8008"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=600,
)

# Database setup


def get_db_connection():
    """Get SQLite database connection."""
    db_path = os.path.join(os.path.dirname(__file__), "..", "data", "dashboard.db")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database tables."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create experiments table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS experiments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            dataset_name TEXT NOT NULL,
            architecture_name TEXT NOT NULL,
            num_clients INTEGER NOT NULL,
            iid BOOLEAN NOT NULL,
            status TEXT DEFAULT 'pending',
            parameters JSON NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create experiment results table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS experiment_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            experiment_id INTEGER NOT NULL,
            client_id INTEGER,
            round INTEGER NOT NULL,
            accuracy REAL,
            loss REAL,
            metrics JSON,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (experiment_id) REFERENCES experiments(id)
        )
    """)

    # Create architectures table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS architectures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            config JSON NOT NULL,
            compatible_datasets TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


# Initialize database on startup
init_db()

# Pydantic models for request/response validation


class ExperimentCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    dataset_name: str
    architecture_name: str
    num_clients: int
    iid: bool
    parameters: Dict[str, Any]


class ExperimentUpdate(BaseModel):
    name: Optional[str]
    description: Optional[str]
    status: Optional[str]
    parameters: Optional[Dict[str, Any]]


class ArchitectureCreate(BaseModel):
    name: str
    description: str = ""
    config: Dict[str, Any]
    compatible_datasets: Optional[List[str]] = []

# API Endpoints


@app.get("/api/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Experiment endpoints


@app.get("/api/experiments", response_model=List[Dict])
def get_experiments():
    """Get all experiments."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM experiments ORDER BY created_at DESC")
    experiments = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return experiments


@app.post("/api/experiments", response_model=Dict)
def create_experiment(experiment: ExperimentCreate):
    """Create a new experiment."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO experiments
            (name, description, dataset_name, architecture_name, num_clients, iid, status, parameters)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            experiment.name,
            experiment.description,
            experiment.dataset_name,
            experiment.architecture_name,
            experiment.num_clients,
            experiment.iid,
            "pending",
            json.dumps(experiment.parameters)
        ))

        experiment_id = cursor.lastrowid
        conn.commit()

        # Return the created experiment
        cursor.execute("SELECT * FROM experiments WHERE id = ?", (experiment_id,))
        created_experiment = dict(cursor.fetchone())

        return created_experiment

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()


@app.get("/api/experiments/{experiment_id}", response_model=Dict)
def get_experiment(experiment_id: int):
    """Get a specific experiment."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM experiments WHERE id = ?", (experiment_id,))
    experiment = cursor.fetchone()
    conn.close()

    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    return dict(experiment)


@app.put("/api/experiments/{experiment_id}", response_model=Dict)
def update_experiment(experiment_id: int, update_data: ExperimentUpdate):
    """Update an experiment."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get current experiment
    cursor.execute("SELECT * FROM experiments WHERE id = ?", (experiment_id,))
    experiment = cursor.fetchone()

    if not experiment:
        conn.close()
        raise HTTPException(status_code=404, detail="Experiment not found")

    try:
        # Build update query
        updates = []
        params = []

        if update_data.name is not None:
            updates.append("name = ?")
            params.append(update_data.name)

        if update_data.description is not None:
            updates.append("description = ?")
            params.append(update_data.description)

        if update_data.status is not None:
            updates.append("status = ?")
            params.append(update_data.status)

        if update_data.parameters is not None:
            updates.append("parameters = ?")
            params.append(json.dumps(update_data.parameters))

        updates.append("updated_at = ?")
        params.append(datetime.now().isoformat())

        params.append(experiment_id)

        query = f"UPDATE experiments SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)
        conn.commit()

        # Return updated experiment
        cursor.execute("SELECT * FROM experiments WHERE id = ?", (experiment_id,))
        updated_experiment = dict(cursor.fetchone())

        return updated_experiment

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()


@app.get("/api/experiments/{experiment_id}/results", response_model=List[Dict])
def get_experiment_results(experiment_id: int):
    """Get results for a specific experiment."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM experiment_results
        WHERE experiment_id = ?
        ORDER BY round, timestamp
    """, (experiment_id,))

    results = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return results


@app.post("/api/experiments/{experiment_id}/results", response_model=Dict)
def add_experiment_result(experiment_id: int, result: Dict):
    """Add a result for an experiment."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Verify experiment exists
    cursor.execute("SELECT id FROM experiments WHERE id = ?", (experiment_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Experiment not found")

    try:
        cursor.execute("""
            INSERT INTO experiment_results
            (experiment_id, client_id, round, accuracy, loss, metrics)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            experiment_id,
            result.get('client_id'),
            result.get('round'),
            result.get('accuracy'),
            result.get('loss'),
            json.dumps(result.get('metrics', {}))
        ))

        result_id = cursor.lastrowid
        conn.commit()

        # Return the created result
        cursor.execute("SELECT * FROM experiment_results WHERE id = ?", (result_id,))
        created_result = dict(cursor.fetchone())

        return created_result

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()

# Architecture endpoints


@app.get("/api/architectures", response_model=List[Dict])
def get_architectures():
    """Get all registered architectures."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM architectures ORDER BY name")
    architectures = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return architectures


@app.post("/api/architectures", response_model=Dict)
def create_architecture(architecture: ArchitectureCreate):
    """Register a new architecture."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO architectures
            (name, description, config, compatible_datasets)
            VALUES (?, ?, ?, ?)
        """, (
            architecture.name,
            architecture.description,
            json.dumps(architecture.config),
            json.dumps(architecture.compatible_datasets)
        ))

        architecture_id = cursor.lastrowid
        conn.commit()

        # Return the created architecture
        cursor.execute("SELECT * FROM architectures WHERE id = ?", (architecture_id,))
        created_architecture = dict(cursor.fetchone())

        return created_architecture

    except sqlite3.IntegrityError:
        conn.rollback()
        raise HTTPException(status_code=400, detail="Architecture with this name already exists")
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()


@app.get("/api/architectures/view/{architecture_name}", response_model=Dict)
def get_architecture(architecture_name: str):
    """Get a specific architecture by name."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM architectures WHERE name = ?", (architecture_name,))
    architecture = cursor.fetchone()
    conn.close()

    if not architecture:
        raise HTTPException(status_code=404, detail="Architecture not found")

    return dict(architecture)


@app.get("/api/architectures/registry")
def get_architecture_registry():
    """Get architectures from ARCH-FL architecture registry."""
    try:
        from src.models.architecture_registry import get_architecture_registry

        registry = get_architecture_registry()
        architectures = registry.list_architectures()

        # Get detailed info for each architecture
        architecture_list = []
        for arch_name in architectures:
            try:
                info = registry.get_architecture_info(arch_name)
                if info:
                    config = info.get("config", {})
                    architecture_list.append({
                        "name": arch_name,
                        "description": info.get("description", ""),
                        "model_type": config.get("name", "Unknown"),
                        "compatible_datasets": info.get("compatible_datasets", [])
                    })
            except:
                pass

        return architecture_list

    except ImportError:
        # Fallback if ARCH-FL core not available
        return [
            {"name": "simple_cnn", "description": "Simple CNN", "model_type": "SimpleCNN", "compatible_datasets": ["pneumoniamnist"]},
            {"name": "medium_cnn", "description": "Medium CNN", "model_type": "ConfigurableCNN", "compatible_datasets": ["mimic_cxr"]},
            {"name": "resnet18", "description": "ResNet18", "model_type": "ResNet18", "compatible_datasets": ["chexpert"]}
        ]


# Dataset endpoints (integration with ARCH-FL core)


@app.get("/api/datasets")
def get_datasets():
    """Get available datasets from ARCH-FL registry."""
    try:
        from src.data.loader_registry import get_data_loader_registry

        registry = get_data_loader_registry()
        datasets = registry.list_loaders()  # This should be list_datasets()

        # Get detailed info for each dataset
        dataset_list = []
        for dataset_name in datasets:
            try:
                info = registry.get_dataset_info(dataset_name)
                if info:
                    dataset_list.append({
                        "name": dataset_name,
                        "description": info.get("description", ""),
                        "supported": info.get("supported", True)
                    })
            except Exception:
                pass

        return dataset_list

    except ImportError:
        # Fallback if ARCH-FL core not available
        return [
            {"name": "PneumoniaMNIST", "description": "Pneumonia MNIST Dataset", "supported": True},
            {"name": "MIMIC-CXR", "description": "MIMIC Chest X-ray Dataset", "supported": True},
            {"name": "CheXpert", "description": "CheXpert Chest X-ray Dataset", "supported": True}
        ]


# WebSocket endpoint for real-time monitoring


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()


@app.websocket("/ws/monitoring")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time experiment monitoring."""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Here you would handle incoming messages
            # For now, just echo back
            await manager.send_personal_message(f"Message received: {data}", websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Root endpoint for testing


@app.get("/")
def read_root():
    """Root endpoint."""
    return {
        "message": "ARCH-FL Dashboard API",
        "version": "1.0.0",
        "docs": "/api/docs",
        "status": "running"
    }


# Add backend endpoint for creating architectures
@app.post("/api/architectures/backend")
def create_architecture_backend(architecture: ArchitectureCreate):
    """Register a new architecture in the ARCH-FL backend registry."""
    try:
        from src.models.architecture_registry import get_architecture_registry
        
        registry = get_architecture_registry()
        
        # Register the architecture
        registry.register_custom_architecture(
            architecture.name,
            architecture.config,
            architecture.description,
            architecture.compatible_datasets
        )
        
        # Return success
        return {
            "status": "success",
            "message": "Architecture registered successfully",
            "architecture": {
                "name": architecture.name,
                "description": architecture.description,
                "model_type": architecture.config.get("name", "Unknown")
            }
        }
        
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="ARCH-FL core not available. Architecture registered in dashboard only."
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to register architecture: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8008, reload=True)
