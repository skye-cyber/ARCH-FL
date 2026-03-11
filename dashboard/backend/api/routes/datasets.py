from fastapi import APIRouter

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.get("/")
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
                    dataset_list.append(
                        {
                            "name": dataset_name,
                            "description": info.get("description", ""),
                            "supported": info.get("supported", True),
                        }
                    )
            except Exception:
                pass

        return dataset_list

    except ImportError:
        # Fallback if ARCH-FL core not available
        return [
            {
                "name": "PneumoniaMNIST",
                "description": "Pneumonia MNIST Dataset",
                "supported": True,
            },
            {
                "name": "MIMIC-CXR",
                "description": "MIMIC Chest X-ray Dataset",
                "supported": True,
            },
            {
                "name": "CheXpert",
                "description": "CheXpert Chest X-ray Dataset",
                "supported": True,
            },
        ]
