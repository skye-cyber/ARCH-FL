import json
from fastapi import APIRouter, HTTPException
from typing import List, Dict
import sqlite3
from backend.models.requests import ArchitectureCreate
from backend.core.db import dbmanager


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
    if not dbmanager.validate_architecture_exists(architecture_name):
        raise HTTPException(status_code=404, detail="Architecture not found")

    # Check if architecture is in use by any experiments
    in_use_count = dbmanager.get_architecture_in_use_count(architecture_name)

    if in_use_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete architecture. It is being used by {in_use_count} experiment(s).",
        )

    # Delete the architecture
    with dbmanager.transaction() as cursor:
        cursor.execute("DELETE FROM architectures WHERE name = ?", (architecture_name,))

    return {
        "status": "deleted",
        "message": "Architecture deleted successfully",
        "architecture_name": architecture_name,
    }


@router.post("/{architecture_name}/duplicate", response_model=Dict)
def duplicate_architecture(architecture_name: str):
    """Duplicate an architecture with a new name."""
    # Get the original architecture
    with dbmanager.transaction() as cursor:
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
    with dbmanager.transaction() as cursor:
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
    with dbmanager.transaction() as cursor:
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
    if not dbmanager.validate_architecture_exists(architecture_name):
        raise HTTPException(status_code=404, detail="Architecture not found")

    # Check if new name already exists (if changed)
    if update_data.name != architecture_name and dbmanager.validate_architecture_exists(update_data.name):
        raise HTTPException(status_code=400, detail="Architecture name already exists")

    # Update the architecture
    with dbmanager.transaction() as cursor:
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

    return {
        "status": "updated",
        "message": "Architecture updated successfully",
        "architecture_name": update_data.name,
    }


@router.post("/", response_model=Dict)
def create_architecture(architecture: ArchitectureCreate):
    """Create architecture in database and optionally register in ARCH-FL registry"""
    
    # Step 1: Validate input
    if not architecture.name or not architecture.config:
        raise HTTPException(status_code=400, detail="Name and config are required")
    
    # Check if architecture already exists
    if dbmanager.validate_architecture_exists(architecture.name):
        raise HTTPException(status_code=400, detail="Architecture name already exists")
    
    # Step 2: Store in database (transaction)
    conn = dbmanager.connection
    cursor = conn.cursor()
    
    try:
        # Insert into database
        cursor.execute(
            """
            INSERT INTO architectures
            (name, description, config, compatible_datasets)
            VALUES (?, ?, ?, ?)
            """,
            (
                architecture.name,
                architecture.description or "",
                json.dumps(architecture.config),
                json.dumps(architecture.compatible_datasets or []),
            ),
        )
        
        architecture_id = cursor.lastrowid
        conn.commit()
        
        # Step 3: Optionally register in ARCH-FL registry
        registry_success = False
        try:
            from src.models.architecture_registry import get_architecture_registry
            registry = get_architecture_registry()
            registry.register_custom_architecture(
                architecture.name,
                architecture.config,
                architecture.description,
                architecture.compatible_datasets,
            )
            registry_success = True
        except ImportError:
            # Registry not available, continue without it
            pass
        
        # Step 4: Return result
        cursor.execute("SELECT * FROM architectures WHERE id = ?", (architecture_id,))
        created = dict(cursor.fetchone())
        
        return {
            "status": "created",
            "database": "success",
            "registry": "success" if registry_success else "unavailable",
            "data": created
        }
        
    except sqlite3.IntegrityError as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=f"Database error: {str(e)}")
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create architecture: {str(e)}")
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
