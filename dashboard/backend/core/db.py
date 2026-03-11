import os
import sqlite3


class DatabaseManager:
    def __init__(self):
        self = self

    @property
    def connection(self):
        """Get SQLite database connection."""
        db_path = os.path.join(os.path.dirname(__file__), "..", "data", "dashboard.db")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn

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
