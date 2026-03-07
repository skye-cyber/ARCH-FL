"""
Dashboard Integration Utilities

This module provides utilities for integrating the ARCH-FL core system with the dashboard.
"""

import json
from typing import Dict, Any, Optional
import sqlite3
import os
from datetime import datetime


class DashboardConnector:
    """Connector for integrating ARCH-FL core with the dashboard database."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize the dashboard connector."""
        if db_path is None:
            # Default path relative to dashboard/data/dashboard.db
            db_path = os.path.join(
                os.path.dirname(__file__),
                "..", "..", "dashboard", "data", "dashboard.db"
            )
        self.db_path = db_path
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    def get_db_connection(self):
        """Get SQLite database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def create_experiment_record(self, experiment_data: Dict[str, Any]) -> int:
        """Create a new experiment record in the dashboard database."""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                """
                INSERT INTO experiments
                (name, description, dataset_name, architecture_name, num_clients, iid, status, parameters)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    experiment_data.get("name", "Unnamed Experiment"),
                    experiment_data.get("description", ""),
                    experiment_data.get("dataset_name", "unknown"),
                    experiment_data.get("architecture_name", "unknown"),
                    experiment_data.get("num_clients", 1),
                    experiment_data.get("iid", True),
                    experiment_data.get("status", "pending"),
                    json.dumps(experiment_data.get("parameters", {})),
                ),
            )
            
            experiment_id = cursor.lastrowid
            conn.commit()
            return experiment_id
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def update_experiment_status(self, experiment_id: int, status: str, 
                                 metrics: Optional[Dict[str, Any]] = None) -> None:
        """Update experiment status and optionally add metrics."""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Update experiment status
            cursor.execute(
                "UPDATE experiments SET status = ?, updated_at = ? WHERE id = ?",
                (status, datetime.now().isoformat(), experiment_id),
            )
            
            # Add metrics if provided
            if metrics:
                cursor.execute(
                    """
                    INSERT INTO experiment_results
                    (experiment_id, client_id, round, accuracy, loss, metrics)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        experiment_id,
                        metrics.get("client_id", None),
                        metrics.get("round", 0),
                        metrics.get("accuracy", None),
                        metrics.get("loss", None),
                        json.dumps(metrics.get("additional_metrics", {})),
                    ),
                )
            
            conn.commit()
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def get_experiment_by_id(self, experiment_id: int) -> Optional[Dict[str, Any]]:
        """Get experiment details by ID."""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM experiments WHERE id = ?", (experiment_id,))
            experiment = cursor.fetchone()
            
            if experiment:
                return dict(experiment)
            return None
            
        finally:
            conn.close()
    
    def add_experiment_result(self, experiment_id: int, result_data: Dict[str, Any]) -> int:
        """Add a result record for an experiment."""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                """
                INSERT INTO experiment_results
                (experiment_id, client_id, round, accuracy, loss, metrics)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    experiment_id,
                    result_data.get("client_id", None),
                    result_data.get("round", 0),
                    result_data.get("accuracy", None),
                    result_data.get("loss", None),
                    json.dumps(result_data.get("metrics", {})),
                ),
            )
            
            result_id = cursor.lastrowid
            conn.commit()
            return result_id
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()


def create_dashboard_callback(experiment_id: int, 
                              dashboard_connector: DashboardConnector) -> ProgressCallback:
    """Create a progress callback function for the coordinator."""
    
    def callback(round_num: int, metrics: Dict[str, float], event_type: str):
        """Callback function to update dashboard with progress."""
        try:
            # Update experiment status
            status = "running"
            if event_type == "aggregation_complete":
                status = "running"
            elif event_type == "training_complete":
                status = "completed"
            
            # Add round information to metrics
            metrics_with_round = {
                "round": round_num,
                "status": status,
                "metrics": metrics
            }
            
            dashboard_connector.update_experiment_status(
                experiment_id, status, metrics_with_round
            )
            
        except Exception as e:
            print(f"Error updating dashboard: {e}")
    
    return callback