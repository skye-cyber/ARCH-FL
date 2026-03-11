import json
from fastapi import APIRouter, HTTPException
from typing import List, Dict
import sqlite3
from backend.models.requests import ArchitectureCreate
from backend.db import dbmanager


router = APIRouter(prefix="/architectures", tags=["architectures"])


@router.get("/", response_model=List[Dict])
def get_architectures():
    """Get all registered architectures."""
    conn = dbmanager.connection
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM architectures ORDER BY name")
    architectures = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return architectures


@router.post("/create")
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
            architecture.compatible_datasets,
        )

        # Return success
        return {
            "status": "success",
            "message": "Architecture registered successfully",
            "architecture": {
                "name": architecture.name,
                "description": architecture.description,
                "model_type": architecture.config.get("name", "Unknown"),
            },
        }

    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="ARCH-FL core not available. Architecture registered in dashboard only.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Failed to register architecture: {str(e)}"
        )


@router.post("/{architecture_name}/delete", response_model=Dict)
def delete_architecture(architecture_name: str):
    """Delete an architecture."""
    # Check if architecture exists
    conn = dbmanager.connection
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM architectures WHERE name = ?", (architecture_name,))
    architecture = cursor.fetchone()

    if not architecture:
        raise HTTPException(status_code=404, detail="Architecture not found")

    # Check if architecture is in use by any experiments
    cursor.execute(
        "SELECT COUNT(*) as count FROM experiments WHERE architecture_name = ?",
        (architecture_name,),
    )
    result = cursor.fetchone()
    in_use_count = result["count"]

    if in_use_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete architecture. It is being used by {in_use_count} experiment(s).",
        )

    # Delete the architecture
    cursor.execute("DELETE FROM architectures WHERE name = ?", (architecture_name,))
    conn.commit()
    conn.close()

    return {
        "status": "deleted",
        "message": "Architecture deleted successfully",
        "architecture_name": architecture_name,
    }


@router.post("/{architecture_name}/duplicate", response_model=Dict)
def duplicate_architecture(architecture_name: str):
    """Duplicate an architecture with a new name."""
    # Get the original architecture
    conn = dbmanager.connection
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM architectures WHERE name = ?", (architecture_name,))
    architecture = cursor.fetchone()

    if not architecture:
        raise HTTPException(status_code=404, detail="Architecture not found")

    architecture_dict = dict(architecture)

    # Generate new name
    base_name = architecture_name
    suffix = 1
    new_name = f"{base_name}_copy"

    # Check if name already exists
    while True:
        cursor.execute(
            "SELECT COUNT(*) as count FROM architectures WHERE name = ?", (new_name,)
        )
        result = cursor.fetchone()
        if result["count"] == 0:
            break
        new_name = f"{base_name}_copy_{suffix}"
        suffix += 1

    # Create the duplicate
    cursor.execute(
        """
        INSERT INTO architectures
        (name, description, config, compatible_datasets)
        VALUES (?, ?, ?, ?)
    """,
        (
            new_name,
            f"Copy of {architecture_dict['description'] or architecture_name}",
            architecture_dict["config"],
            architecture_dict["compatible_datasets"],
        ),
    )

    conn.commit()
    conn.close()

    return {
        "status": "created",
        "message": "Architecture duplicated successfully",
        "original_name": architecture_name,
        "new_name": new_name,
    }


@router.post("/{architecture_name}/update", response_model=Dict)
def update_architecture(architecture_name: str, update_data: ArchitectureCreate):
    """Update an architecture."""
    # Check if architecture exists
    conn = dbmanager.connection
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM architectures WHERE name = ?", (architecture_name,))
    architecture = cursor.fetchone()

    if not architecture:
        raise HTTPException(status_code=404, detail="Architecture not found")

    # Update the architecture
    cursor.execute(
        """
        UPDATE architectures
        SET name = ?, description = ?, config = ?, compatible_datasets = ?
        WHERE name = ?
    """,
        (
            update_data.name,
            update_data.description,
            json.dumps(update_data.config),
            json.dumps(update_data.compatible_datasets),
            architecture_name,
        ),
    )

    conn.commit()
    conn.close()

    return {
        "status": "updated",
        "message": "Architecture updated successfully",
        "architecture_name": update_data.name,
    }


@router.post("/", response_model=Dict)
def create_architecture(architecture: ArchitectureCreate):
    """Register a new architecture."""
    conn = dbmanager.connection
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO architectures
            (name, description, config, compatible_datasets)
            VALUES (?, ?, ?, ?)
        """,
            (
                architecture.name,
                architecture.description,
                json.dumps(architecture.config),
                json.dumps(architecture.compatible_datasets),
            ),
        )

        architecture_id = cursor.lastrowid
        conn.commit()

        # Return the created architecture
        cursor.execute("SELECT * FROM architectures WHERE id = ?", (architecture_id,))
        created_architecture = dict(cursor.fetchone())

        return created_architecture

    except sqlite3.IntegrityError:
        conn.rollback()
        raise HTTPException(
            status_code=400, detail="Architecture with this name already exists"
        )
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()


@router.get("/view/{architecture_name}", response_model=Dict)
def get_architecture(architecture_name: str):
    """Get a specific architecture by name."""
    conn = dbmanager.connection
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM architectures WHERE name = ?", (architecture_name,))
    architecture = cursor.fetchone()
    conn.close()

    if not architecture:
        raise HTTPException(status_code=404, detail="Architecture not found")

    return dict(architecture)


@router.get("/registry")
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
                    architecture_list.append(
                        {
                            "name": arch_name,
                            "description": info.get("description", ""),
                            "model_type": config.get("name", "Unknown"),
                            "compatible_datasets": info.get("compatible_datasets", []),
                        }
                    )
            except:
                pass

        return architecture_list

    except ImportError:
        # Fallback if ARCH-FL core not available
        return [
            {
                "name": "simple_cnn",
                "description": "Simple CNN",
                "model_type": "SimpleCNN",
                "compatible_datasets": ["pneumoniamnist"],
            },
            {
                "name": "medium_cnn",
                "description": "Medium CNN",
                "model_type": "ConfigurableCNN",
                "compatible_datasets": ["mimic_cxr"],
            },
            {
                "name": "resnet18",
                "description": "ResNet18",
                "model_type": "ResNet18",
                "compatible_datasets": ["chexpert"],
            },
        ]
