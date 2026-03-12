from fastapi import APIRouter
from backend.core.db import dbmanager

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.get("/")
def get_datasets():
    """Get available datasets from database (discovered from filesystem)."""
    conn = dbmanager.connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM datasets ORDER BY name")
    datasets = [dict(row) for row in cursor.fetchall()]
    conn.close()

    # Format the response
    result = []
    for dataset in datasets:
        result.append(
            {
                "name": dataset["name"],
                "description": dataset["description"],
                "metadata": dataset.get("metadata", {}),
                "created_at": dataset.get("created_at"),
            }
        )

    return result
