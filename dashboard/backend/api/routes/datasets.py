from fastapi import APIRouter
from backend.core.db import dbmanager
import yaml
from pathlib import Path
from backend.config.settings import settings
from backend.utils.logger import logger
import json
from backend.utils.file_utils import get_folder_size, format_size

router = APIRouter(prefix="/datasets", tags=["datasets"])


def _discover_datasets_from_filesystem():
    """Discover datasets from filesystem and register them in database."""
    dataset_base_path = settings.DATASET_BASE_PATH
    base_path = Path(dataset_base_path)

    if not base_path.exists():
        logger.warning(f"Dataset base path {dataset_base_path} does not exist")
        return []

    discovered_datasets = []

    for dataset_dir in base_path.iterdir():
        if not dataset_dir.is_dir():
            continue

        dataset_name = dataset_dir.name

        # Check if this is a valid dataset directory
        # dataset_config_dir = dataset_dir / "data"
        # logger.info(f"DIR: {dataset_config_dir.exists()}")
        # if not dataset_config_dir.exists():
        #     continue

        config_file = dataset_dir / "datasetinfo.yml"
        data_dir = dataset_dir / "data"

        # Validate dataset structure
        if not config_file.exists():
            logger.debug(f"Dataset {dataset_name}: missing datasetinfo.yml")
            continue

        if not data_dir.exists() or not any(data_dir.iterdir()):
            logger.debug(f"Dataset {dataset_name}: data folder is empty")
            continue

        # Load dataset configuration
        try:
            with open(config_file, "r") as f:
                dataset_config = yaml.safe_load(f)

            # Extract relevant information
            dataset_info = {
                "name": dataset_name,
                "description": dataset_config.get("description", ""),
                "metadata": {
                    "num_classes": dataset_config.get("num_classes"),
                    "input_size": dataset_config.get("input_size"),
                    "channels": dataset_config.get("channels"),
                    "task": dataset_config.get("task"),
                    "split": dataset_config.get("split"),
                    "location": str(data_dir.absolute()),
                },
            }

            discovered_datasets.append(dataset_info)

        except Exception as e:
            logger.warning(f"Failed to load dataset config for {dataset_name}: {e}")
            continue

    if not discovered_datasets:
        logger.warning(f"No datasets discovered in {dataset_base_path}")

    return discovered_datasets


@router.get("/")
def get_datasets():
    """Get available datasets from database (discovered from filesystem if empty)."""
    conn = dbmanager.connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM datasets")
    count = cursor.fetchone()[0]

    # If database is empty, discover datasets from filesystem and register them
    if count == 0:
        discovered_datasets = _discover_datasets_from_filesystem()

        if discovered_datasets:
            # Register discovered datasets in database
            for dataset in discovered_datasets:
                with dbmanager.transaction() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO datasets 
                        (name, description, metadata)
                        VALUES (?, ?, ?)
                        """,
                        (
                            dataset["name"],
                            dataset["description"],
                            str(dataset["metadata"]),  # Convert to string for SQLite
                        ),
                    )

            # Return the discovered datasets
            result = []
            for dataset in discovered_datasets:
                result.append(
                    {
                        "name": dataset["name"],
                        "description": dataset["description"],
                        "metadata": dataset["metadata"],
                        "created_at": None,  # Just discovered
                    }
                )

            return result

    cursor.execute("SELECT * FROM datasets ORDER BY name")
    datasets = [dict(row) for row in cursor.fetchall()]

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


@router.get("/info/{name}")
def get_dataset(name: str):
    """Get available datasets from database (discovered from filesystem if empty)."""
    conn = dbmanager.connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM datasets WHERE name=? ORDER BY name", (name,))
    dataset = dict(cursor.fetchone())

    # Format the response
    metadata = json.loads(dataset.get("metadata", {}))
    path = metadata.get("location", None)
    size = 0
    size_human = 0
    # Calculate dataset size
    if path:
        abs_path = Path(path).absolute().as_posix()
        size = get_folder_size(abs_path)
        size_human = format_size(size)

    result = {
        "name": dataset["name"],
        "description": dataset["description"],
        "metadata": dataset.get("metadata", {}),
        "size": {"human": size_human, "raw": size},
        "created_at": dataset.get("created_at"),
    }

    return result
