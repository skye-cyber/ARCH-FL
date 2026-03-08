#!/usr/bin/env python3

import sys
import os

# Add the project root to path
sys.path.insert(0, os.path.dirname(__file__))

print("🚀 Testing MIMIC-CXR integration with federated learning...")

try:
    from src.models.architectures import SimpleCNN
    from src.data.mimic_cxr_loader import create_mimic_cxr_data_loaders
    from src.core.coordinator import Coordinator
    from src.core.client import Client
    from src.training.fedavg import FederatedTrainer

    print("✓ All imports successful")

    # Create data loaders with MIMIC-CXR
    print("\n📊 Creating MIMIC-CXR data loaders...")
    client_loaders, test_loader = create_mimic_cxr_data_loaders(
        num_clients=3,
        max_samples=100,  # Small subset for testing
        batch_size=16,
        iid=True
    )

    print(f"✅ Created {len(client_loaders)} client loaders")
    print(f"✅ Test loader: {len(test_loader.dataset)} samples")

    # Create clients
    print("\n👥 Creating federated learning clients...")
    clients = []
    for i, loader in enumerate(client_loaders):
        client = Client(
            client_id=i,
            model=SimpleCNN(num_classes=2),
            train_loader=loader
        )
        clients.append(client)
        print(f"✅ Client {i} created with {len(loader.dataset)} samples")

    # Create coordinator and trainer
    print("\n🤖 Creating coordinator and federated trainer...")
    global_model = SimpleCNN(num_classes=2)
    coordinator = Coordinator(global_model)

    trainer = FederatedTrainer(coordinator, clients, test_loader, device="cpu")
    print("✅ Federated trainer created")

    # Run a few federated training rounds
    print("\n🏋️ Running federated training with MIMIC-CXR...")
    num_rounds = 2

    for round_num in range(num_rounds):
        print(f"\n--- Round {round_num + 1}/{num_rounds} ---")

        # Select all clients for this round
        client_indices = list(range(len(clients)))

        # Train round
        accuracy = trainer.train_round(
            client_indices=client_indices,
            local_epochs=1,
            lr=0.01
        )

        print(f"✅ Round {round_num + 1} completed with accuracy: {accuracy:.2f}%")

    # Test DP integration
    print("\n🔒 Testing DP integration with MIMIC-CXR...")
    from src.core.client import XClient

    dp_config = {
        'enabled': True,
        'epsilon': 4.0,
        'delta': 1e-5,
        'max_grad_norm': 1.0
    }

    # Create DP client
    dp_client = XClient(
        client_id=99,
        model=SimpleCNN(num_classes=2),
        train_loader=client_loaders[0],  # Use first client's data
        device="cpu",
        dp_config=dp_config
    )

    # Test DP training
    global_params = coordinator.get_global_model()
    update, privacy_info = dp_client.local_train(global_params, local_epochs=1, lr=0.01)
    print(f"✅ DP client training completed with privacy: ε={privacy_info['epsilon']:.2f}")

    print("\n🎉 MIMIC-CXR integration test completed successfully!")
    print("\n📋 Summary:")
    print("   • Dataset: MIMIC-CXR (100 samples subset)")
    print(f"   • Clients: {len(clients)} with IID partitioning")
    print(f"   • Training rounds: {num_rounds}")
    print("   • DP integration: ✅ Working")
    print(f"   • Final accuracy: {accuracy:.2f}%")
    print("   • Image size: 224x224 grayscale")
    print("   • Target pathology: Pneumonia")

except Exception as e:
    print(f"❌ Integration test failed: {e}")
    import traceback
    traceback.print_exc()

print("\n🏁 MIMIC-CXR integration test completed.")
