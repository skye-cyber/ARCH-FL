import os
import sqlite3
from contextlib import contextmanager


class DatabaseManager:
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(__file__), "..", "data", "dashboard.db")
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    def connection(self):
        """Get SQLite database connection with foreign key enforcement."""
        conn = sqlite3.connect(self.db_path)
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
                (architecture_name,)
            )
            return cursor.fetchone()[0] > 0

    def validate_dataset_exists(self, dataset_name: str) -> bool:
        """Check if dataset exists in database."""
        with self.transaction() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM datasets WHERE name = ?",
                (dataset_name,)
            )
            return cursor.fetchone()[0] > 0

    def get_architecture_in_use_count(self, architecture_name: str) -> int:
        """Get count of experiments using this architecture."""
        with self.transaction() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM experiments WHERE architecture_name = ?",
                (architecture_name,)
            )
            return cursor.fetchone()[0]

    def init(self):
        """Initialize database tables."""
        conn = self.connection
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


dbmanager = DatabaseManager()
