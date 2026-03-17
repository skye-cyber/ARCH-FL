import json
from typing import Optional, List, Dict, Any
from datetime import datetime
from .logger import logger
from ..core.db import dbmanager


async def get_experiment_by_id(experiment_id: int) -> Optional[Dict[str, Any]]:
    """
    Fetch experiment details by ID
    """
    try:
        conn = dbmanager.connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                e.*,
                a.name as architecture_name,
                a.config as architecture_config,
                d.name as dataset_name,
                d.metadata as dataset_metadata
            FROM experiments e
            LEFT JOIN architectures a ON e.architecture_id = a.id
            LEFT JOIN datasets d ON e.dataset_id = d.id
            WHERE e.id = ?
        """,
            (experiment_id,),
        )

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        # Convert row to dict
        experiment = dict(row)

        # Parse JSON fields
        if experiment.get("parameters") and isinstance(experiment["parameters"], str):
            try:
                experiment["parameters"] = json.loads(experiment["parameters"])
            except Exception:
                pass

        if experiment.get("architecture_config") and isinstance(
            experiment["architecture_config"], str
        ):
            try:
                experiment["architecture_config"] = json.loads(
                    experiment["architecture_config"]
                )
            except Exception:
                pass

        if experiment.get("dataset_metadata") and isinstance(
            experiment["dataset_metadata"], str
        ):
            try:
                experiment["dataset_metadata"] = json.loads(
                    experiment["dataset_metadata"]
                )
            except Exception:
                pass

        return experiment

    except Exception as e:
        logger.error(f"Error fetching experiment {experiment_id}: {e}")
        return None


async def get_experiment_results(experiment_id: int) -> List[Dict[str, Any]]:
    """
    Fetch results from experiment_results table
    """
    try:
        conn = dbmanager.connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                id,
                experiment_id,
                total_rounds,
                client_count,
                rounds_completed,
                accuracy,
                loss,
                metrics,
                timestamp
            FROM experiment_results
            WHERE experiment_id = ?
            ORDER BY timestamp ASC
        """,
            (experiment_id,),
        )

        rows = cursor.fetchall()
        conn.close()

        results = []
        for row in rows:
            result = dict(row)
            # Parse metrics JSON if it exists
            if result.get("metrics") and isinstance(result["metrics"], str):
                try:
                    result["metrics"] = json.loads(result["metrics"])
                except Exception:
                    pass
            results.append(result)

        return results

    except Exception as e:
        logger.error(f"Error fetching experiment results for {experiment_id}: {e}")
        return []


async def get_client_results(
    experiment_id: int,
    limit: Optional[int] = None,
    client_id: Optional[int] = None,
    round_num: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Fetch results from client_results table with optional filters
    """
    try:
        conn = dbmanager.connection()
        cursor = conn.cursor()

        query = """
            SELECT
                id,
                experiment_id,
                client_id,
                round,
                accuracy,
                loss,
                metrics,
                timestamp
            FROM client_results
            WHERE experiment_id = ?
        """
        params = [experiment_id]

        if client_id is not None:
            query += " AND client_id = ?"
            params.append(client_id)

        if round_num is not None:
            query += " AND round = ?"
            params.append(round_num)

        query += " ORDER BY round ASC, client_id ASC, timestamp ASC"

        if limit:
            query += " LIMIT ?"
            params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        results = []
        for row in rows:
            result = dict(row)
            # Parse metrics JSON if it exists
            if result.get("metrics") and isinstance(result["metrics"], str):
                try:
                    result["metrics"] = json.loads(result["metrics"])
                except Exception:
                    pass
            results.append(result)

        return results

    except Exception as e:
        logger.error(f"Error fetching client results for {experiment_id}: {e}")
        return []


async def get_client_summary(experiment_id: int) -> Dict[str, Any]:
    """
    Get summary statistics for all clients in an experiment
    """
    try:
        conn = dbmanager.connection()
        cursor = conn.cursor()

        # Get all client results
        cursor.execute(
            """
            SELECT
                client_id,
                COUNT(*) as total_updates,
                MAX(round) as last_round,
                MAX(accuracy) as best_accuracy,
                MIN(loss) as best_loss,
                AVG(accuracy) as avg_accuracy,
                AVG(loss) as avg_loss
            FROM client_results
            WHERE experiment_id = ?
            GROUP BY client_id
            ORDER BY client_id
        """,
            (experiment_id,),
        )

        rows = cursor.fetchall()
        conn.close()

        summary = {}
        for row in rows:
            data = dict(row)
            client_id = data.pop("client_id")
            summary[client_id] = data

        return summary

    except Exception as e:
        logger.error(f"Error fetching client summary for {experiment_id}: {e}")
        return {}


async def get_round_summary(experiment_id: int) -> List[Dict[str, Any]]:
    """
    Get summary statistics for each round
    """
    try:
        conn = dbmanager.connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                round,
                COUNT(DISTINCT client_id) as clients_participated,
                AVG(accuracy) as avg_accuracy,
                AVG(loss) as avg_loss,
                MAX(accuracy) as max_accuracy,
                MIN(loss) as min_loss,
                COUNT(*) as total_updates
            FROM client_results
            WHERE experiment_id = ?
            GROUP BY round
            ORDER BY round
        """,
            (experiment_id,),
        )

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    except Exception as e:
        logger.error(f"Error fetching round summary for {experiment_id}: {e}")
        return []


async def get_experiment_metrics(experiment_id: int) -> Dict[str, Any]:
    """
    Get comprehensive metrics for an experiment
    """
    try:
        # Get experiment details
        experiment = await get_experiment_by_id(experiment_id)
        if not experiment:
            return {}

        # Get results
        client_results = await get_client_results(experiment_id)
        experiment_results = await get_experiment_results(experiment_id)

        # Get summaries
        client_summary = await get_client_summary(experiment_id)
        round_summary = await get_round_summary(experiment_id)

        # Calculate overall metrics
        total_rounds = experiment.get("parameters", {}).get("num_rounds", 0)
        completed_rounds = (
            len(set(r["round"] for r in client_results)) if client_results else 0
        )

        # Calculate accuracy and loss trends
        accuracy_trend = []
        loss_trend = []

        if round_summary:
            for round_data in round_summary:
                accuracy_trend.append(
                    {"round": round_data["round"], "value": round_data["avg_accuracy"]}
                )
                loss_trend.append(
                    {"round": round_data["round"], "value": round_data["avg_loss"]}
                )

        return {
            "experiment_id": experiment_id,
            "name": experiment.get("name"),
            "status": experiment.get("status"),
            "progress": {
                "completed_rounds": completed_rounds,
                "total_rounds": total_rounds,
                "percentage": int((completed_rounds / total_rounds * 100))
                if total_rounds > 0
                else 0,
            },
            "metrics": {
                "best_accuracy": max(
                    [
                        r.get("accuracy", 0)
                        for r in experiment_results
                        if r.get("accuracy")
                    ]
                )
                if experiment_results
                else None,
                "best_loss": min(
                    [
                        r.get("loss", float("inf"))
                        for r in experiment_results
                        if r.get("loss")
                    ]
                )
                if experiment_results
                else None,
                "final_accuracy": experiment_results[-1].get("accuracy")
                if experiment_results
                else None,
                "final_loss": experiment_results[-1].get("loss")
                if experiment_results
                else None,
            },
            "clients": {
                "total": experiment.get("num_clients", 0),
                "active": len(
                    [
                        c
                        for c in client_summary.values()
                        if c.get("last_round") == completed_rounds
                    ]
                ),
                "summary": client_summary,
            },
            "rounds": round_summary,
            "trends": {"accuracy": accuracy_trend, "loss": loss_trend},
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error getting experiment metrics for {experiment_id}: {e}")
        return {}
