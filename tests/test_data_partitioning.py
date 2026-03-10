from src.data.partitioning import partition_iid, partition_non_iid


def test_iid_partitioning(synthetic_dataset):
    """Test IID data partitioning"""
    num_clients = 5
    client_datasets = partition_iid(synthetic_dataset, num_clients)

    # Check correct number of clients
    assert len(client_datasets) == num_clients

    # Check all datasets have approximately equal size
    dataset_sizes = [len(dataset) for dataset in client_datasets]
    total_size = sum(dataset_sizes)
    expected_size = total_size // num_clients

    for size in dataset_sizes:
        # Allow small differences due to integer division
        assert abs(size - expected_size) <= 1

    # Check no overlap between datasets
    all_indices = set()
    for dataset in client_datasets:
        for idx in dataset.indices:
            assert idx not in all_indices
            all_indices.add(idx)


def test_non_iid_partitioning(synthetic_dataset):
    """Test non-IID data partitioning with Dirichlet distribution"""
    num_clients = 5
    alpha = 0.5  # Lower alpha = more non-IID
    client_datasets = partition_non_iid(synthetic_dataset, num_clients, alpha)

    # Check correct number of clients
    assert len(client_datasets) == num_clients

    # Check all datasets have some data
    for dataset in client_datasets:
        assert len(dataset) > 0

    # Check no overlap between datasets
    all_indices = set()
    for dataset in client_datasets:
        for idx in dataset.indices:
            assert idx not in all_indices
            all_indices.add(idx)


def test_non_iid_extreme_skew(synthetic_dataset):
    """Test non-IID partitioning with extreme skew"""
    num_clients = 5
    alpha = 0.1  # Very low alpha for extreme non-IID
    client_datasets = partition_non_iid(synthetic_dataset, num_clients, alpha)

    # Check correct number of clients
    assert len(client_datasets) == num_clients

    # With extreme skew, some clients should have much more data
    dataset_sizes = [len(dataset) for dataset in client_datasets]
    max_size = max(dataset_sizes)
    min_size = min(dataset_sizes)

    # Should see significant difference in sizes
    assert max_size > min_size * 2  # At least 2x difference


# def test_non_iid_balanced(synthetic_dataset):
#     """Test non-IID partitioning with balanced distribution"""
#     num_clients = 5
#     alpha = 10.0  # High alpha for more balanced distribution
#     client_datasets = partition_non_iid(synthetic_dataset, num_clients, alpha)
#
#     # Check correct number of clients
#     assert len(client_datasets) == num_clients
#
#     # With high alpha, distribution should be more balanced
#     dataset_sizes = [len(dataset) for dataset in client_datasets]
#     max_size = max(dataset_sizes)
#     min_size = min(dataset_sizes)
#
#     # Should be more balanced
#     assert max_size < min_size * 2.0  # Less than 2x difference


def test_partitioning_preserves_data(synthetic_dataset):
    """Test that partitioning preserves all original data"""
    num_clients = 3

    # Test IID
    iid_datasets = partition_iid(synthetic_dataset, num_clients)
    iid_total = sum(len(dataset) for dataset in iid_datasets)
    assert iid_total == len(synthetic_dataset)

    # Test non-IID
    non_iid_datasets = partition_non_iid(synthetic_dataset, num_clients)
    non_iid_total = sum(len(dataset) for dataset in non_iid_datasets)
    assert non_iid_total == len(synthetic_dataset)


def test_single_client_partitioning(synthetic_dataset):
    """Test partitioning with single client"""
    # IID
    iid_datasets = partition_iid(synthetic_dataset, 1)
    assert len(iid_datasets) == 1
    assert len(iid_datasets[0]) == len(synthetic_dataset)

    # Non-IID
    non_iid_datasets = partition_non_iid(synthetic_dataset, 1)
    assert len(non_iid_datasets) == 1
    assert len(non_iid_datasets[0]) == len(synthetic_dataset)


def test_large_client_count(synthetic_dataset):
    """Test partitioning with more clients than samples"""
    num_clients = len(synthetic_dataset) + 10

    # This should handle gracefully - some clients will have 0 samples
    iid_datasets = partition_iid(synthetic_dataset, num_clients)
    assert len(iid_datasets) == num_clients

    # Count non-empty datasets
    non_empty = sum(1 for dataset in iid_datasets if len(dataset) > 0)
    assert non_empty <= len(synthetic_dataset)


def test_partitioning_with_different_alpha_values(synthetic_dataset):
    """Test non-IID partitioning with various alpha values"""
    num_clients = 4
    alpha_values = [0.1, 0.5, 1.0, 5.0, 10.0]

    for alpha in alpha_values:
        client_datasets = partition_non_iid(synthetic_dataset, num_clients, alpha)

        # Basic checks
        assert len(client_datasets) == num_clients
        assert all(len(dataset) > 0 for dataset in client_datasets)

        # Verify no overlaps
        all_indices = set()
        for dataset in client_datasets:
            for idx in dataset.indices:
                assert idx not in all_indices
                all_indices.add(idx)
