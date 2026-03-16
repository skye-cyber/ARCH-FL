from pathlib import Path
import sqlite3
import json
from contextlib import contextmanager
from ..utils.logger import logger


class DatabaseManager:
    def __init__(self):
        self.db_path = Path(__file__).parent.parent / "data/dashboard.db"
        self.db_path.parent.mkdir(exist_ok=True, parents=True)
        self._initialized = False

    def connection(self):
        """Get SQLite database connection with foreign key enforcement."""
        conn = sqlite3.connect(self.db_path.as_posix())
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")

        return conn

    @contextmanager
    def transaction(self):
        """Context manager for database transactions."""
        conn = self.connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def validate_architecture_exists(self, architecture_name: str) -> bool:
        """Check if architecture exists in database."""
        with self.transaction() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM architectures WHERE name = ?",
                (architecture_name,),
            )
            return cursor.fetchone()[0] > 0

    def validate_dataset_exists(self, dataset_name: str) -> bool:
        """Check if dataset exists in database."""
        with self.transaction() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM datasets WHERE name = ?", (dataset_name,)
            )
            return cursor.fetchone()[0] > 0

    def validate_experiment_exists(self, experiment_id: int) -> bool:
        """Check if experiment exists in database."""
        with self.transaction() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM experiments WHERE id = ?", (experiment_id,)
            )
            return cursor.fetchone()[0] > 0

    def validate_experiment_status(
        self, experiment_id: int, expected_status: str
    ) -> bool:
        """Check if experiment has the expected status."""
        with self.transaction() as cursor:
            cursor.execute(
                "SELECT status FROM experiments WHERE id = ?", (experiment_id,)
            )
            result = cursor.fetchone()
            return result and result[0] == expected_status

    def validate_architecture_compatibility(
        self, architecture_name: str, dataset_name: str
    ) -> bool:
        """Check if architecture is compatible with dataset."""
        with self.transaction() as cursor:
            cursor.execute(
                "SELECT compatible_datasets FROM architectures WHERE name = ?",
                (architecture_name,),
            )
            result = cursor.fetchone()
            if not result:
                return False

            compatible_datasets = json.loads(result[0] or "[]")
            if not compatible_datasets:
                return True  # No restrictions

            return dataset_name in compatible_datasets

    def get_architecture_in_use_count(self, architecture_name: str) -> int:
        """Get count of experiments using this architecture."""
        with self.transaction() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM experiments WHERE architecture_name = ?",
                (architecture_name,),
            )
            return cursor.fetchone()[0]

    def _register_builtin_architectures(self):
        """Register built-in architectures from registry if not already in database."""
        try:
            from src.models.architecture_registry import get_architecture_registry

            print("...")
            registry = get_architecture_registry()
            architectures = registry.list_architectures()
            print(architectures)

            for arch_name in architectures:
                if not self.validate_architecture_exists(arch_name):
                    arch_info = registry.get_architecture_info(arch_name)
                    if arch_info:
                        config = arch_info.get("config", {})
                        description = arch_info.get("description", "")
                        compatible_datasets = arch_info.get("compatible_datasets", [])

                        with self.transaction() as cursor:
                            cursor.execute(
                                """
                                INSERT INTO architectures 
                                (name, description, config, compatible_datasets)
                                VALUES (?, ?, ?, ?)
                                """,
                                (
                                    arch_name,
                                    description,
                                    json.dumps(config),
                                    json.dumps(compatible_datasets),
                                ),
                            )
        except ImportError:
            # If ARCH-FL core not available, register fallback architectures
            fallback_architectures = [
                {
                    "name": "simple_cnn",
                    "description": "Simple CNN for basic medical imaging tasks",
                    "config": {
                        "name": "SimpleCNN",
                        "num_classes": 2,
                        "input_shape": [1, 28, 28],
                        "architecture": {
                            "conv_layers": [
                                {
                                    "out_channels": 32,
                                    "kernel_size": 3,
                                    "stride": 1,
                                    "padding": 1,
                                },
                                {
                                    "out_channels": 64,
                                    "kernel_size": 3,
                                    "stride": 1,
                                    "padding": 1,
                                },
                            ],
                            "fc_layers": [{"out_features": 128}, {"out_features": 2}],
                        },
                    },
                    "compatible_datasets": ["pneumoniamnist"],
                },
                {
                    "name": "medium_cnn",
                    "description": "Medium CNN for moderate complexity medical imaging",
                    "config": {
                        "name": "ConfigurableCNN",
                        "num_classes": 2,
                        "input_shape": [1, 224, 224],
                        "architecture": {
                            "conv_layers": [
                                {
                                    "out_channels": 32,
                                    "kernel_size": 3,
                                    "stride": 2,
                                    "padding": 1,
                                },
                                {
                                    "out_channels": 64,
                                    "kernel_size": 3,
                                    "stride": 2,
                                    "padding": 1,
                                },
                                {
                                    "out_channels": 128,
                                    "kernel_size": 3,
                                    "stride": 2,
                                    "padding": 1,
                                },
                            ],
                            "fc_layers": [{"out_features": 256}, {"out_features": 2}],
                        },
                    },
                    "compatible_datasets": ["mimic_cxr"],
                },
                {
                    "name": "resnet18",
                    "description": "ResNet18 with medical imaging modifications",
                    "config": {
                        "name": "ResNet18",
                        "num_classes": 2,
                        "input_shape": [1, 224, 224],
                        "pretrained": False,
                    },
                    "compatible_datasets": ["chexpert", "mimic_cxr"],
                },
            ]

            for arch in fallback_architectures:
                if not self.validate_architecture_exists(arch["name"]):
                    with self.transaction() as cursor:
                        cursor.execute(
                            """
                            INSERT INTO architectures 
                            (name, description, config, compatible_datasets)
                            VALUES (?, ?, ?, ?)
                            """,
                            (
                                arch["name"],
                                arch["description"],
                                json.dumps(arch["config"]),
                                json.dumps(arch["compatible_datasets"]),
                            ),
                        )

    def _register_builtin_datasets(self):
        """Register built-in datasets from filesystem by discovering dataset folders."""
        from backend.api.routes.datasets import _discover_datasets_from_filesystem

        try:
            discovered_datasets = _discover_datasets_from_filesystem()

            # Register discovered datasets in database
            for dataset in discovered_datasets:
                if not self.validate_dataset_exists(dataset["name"]):
                    with self.transaction() as cursor:
                        cursor.execute(
                            """
                            INSERT INTO datasets 
                            (name, description, metadata)
                            VALUES (?, ?, ?)
                            """,
                            (
                                dataset["name"],
                                dataset["description"],
                                json.dumps(dataset["metadata"]),
                            ),
                        )
                        logger.info(f"Registered dataset: {dataset['name']}")

        except Exception as e:
            logger.error(f"Error discovering datasets: {e}")

    def init(self):
        """Initialize database tables and register pre-existing architectures/datasets."""
        if self._initialized:
            return

        conn = self.connection()
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

        # Create datasets table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS datasets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                metadata JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()

        # Register pre-existing architectures and datasets from registries
        self._register_builtin_architectures()
        self._register_builtin_datasets()

        self._initialized = True


dbmanager = DatabaseManager()
