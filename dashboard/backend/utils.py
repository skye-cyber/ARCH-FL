from models import ArchitectureCreate


def register_architecture(architecture: ArchitectureCreate):
    try:
        from src.models.architecture_registry import get_architecture_registry
        registry = get_architecture_registry()
        registry.register_custom_architecture(
            arch_name=architecture.name,
            config=architecture.config,
            compatible_datasets=architecture.compatible_datasets
        )
        return True
    except Exception:
        return False
