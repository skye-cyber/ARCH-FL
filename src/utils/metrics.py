import torch
import torch.nn as nn
from typing import Tuple


def calculate_accuracy(model: torch.nn.Module, data_loader: torch.utils.data.DataLoader,
                       device: str = "cpu") -> float:
    """
    Calculate accuracy of a model on a given dataset.

    Args:
        model: PyTorch model to evaluate
        data_loader: DataLoader containing the evaluation data
        device: Device to run evaluation on

    Returns:
        Accuracy as a float between 0 and 1
    """
    model.eval()
    correct = 0
    total = 0

    with torch.no_grad():
        for data, target in data_loader:
            data, target = data.to(device), target.to(device)
            output = model(data)
            _, predicted = torch.max(output.data, 1)
            total += target.size(0)
            correct += (predicted == target).sum().item()

    return correct / total if total > 0 else 0.0


def calculate_loss(model: torch.nn.Module, data_loader: torch.utils.data.DataLoader,
                   criterion: nn.Module, device: str = "cpu") -> float:
    """
    Calculate loss of a model on a given dataset.

    Args:
        model: PyTorch model to evaluate
        data_loader: DataLoader containing the evaluation data
        criterion: Loss function to use
        device: Device to run evaluation on

    Returns:
        Average loss as a float
    """
    model.eval()
    total_loss = 0.0
    total_samples = 0

    with torch.no_grad():
        for data, target in data_loader:
            data, target = data.to(device), target.to(device)
            output = model(data)
            loss = criterion(output, target)
            total_loss += loss.item() * data.size(0)
            total_samples += data.size(0)

    return total_loss / total_samples if total_samples > 0 else 0.0


def calculate_precision_recall(model: torch.nn.Module, data_loader: torch.utils.data.DataLoader,
                               device: str = "cpu", num_classes: int = 2) -> Tuple[float, float]:
    """
    Calculate precision and recall for multi-class classification.

    Args:
        model: PyTorch model to evaluate
        data_loader: DataLoader containing the evaluation data
        device: Device to run evaluation on
        num_classes: Number of classes

    Returns:
        Tuple of (precision, recall) as floats
    """
    model.eval()
    true_positives = [0] * num_classes
    false_positives = [0] * num_classes
    false_negatives = [0] * num_classes

    with torch.no_grad():
        for data, target in data_loader:
            data, target = data.to(device), target.to(device)
            output = model(data)
            _, predicted = torch.max(output.data, 1)

            for i in range(num_classes):
                # True positives: predicted = i and target = i
                true_positives[i] += ((predicted == i) & (target == i)).sum().item()
                # False positives: predicted = i but target != i
                false_positives[i] += ((predicted == i) & (target != i)).sum().item()
                # False negatives: predicted != i but target = i
                false_negatives[i] += ((predicted != i) & (target == i)).sum().item()

    # Calculate macro-averaged precision and recall
    precision_sum = 0.0
    recall_sum = 0.0
    valid_classes = 0

    for i in range(num_classes):
        if true_positives[i] + false_positives[i] > 0:
            precision_sum += true_positives[i] / (true_positives[i] + false_positives[i])
            valid_classes += 1
        if true_positives[i] + false_negatives[i] > 0:
            recall_sum += true_positives[i] / (true_positives[i] + false_negatives[i])

    precision = precision_sum / valid_classes if valid_classes > 0 else 0.0
    recall = recall_sum / valid_classes if valid_classes > 0 else 0.0

    return precision, recall


def calculate_f1_score(precision: float, recall: float) -> float:
    """
    Calculate F1 score from precision and recall.

    Args:
        precision: Precision value
        recall: Recall value

    Returns:
        F1 score as a float
    """
    if precision + recall == 0:
        return 0.0
    return 2 * (precision * recall) / (precision + recall)
