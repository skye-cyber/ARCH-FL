import matplotlib.pyplot as plt
import numpy as np
from typing import List, Dict, Any


def plot_training_curve(train_losses: List[float], val_losses: List[float] = None,
                       train_acc: List[float] = None, val_acc: List[float] = None,
                       title: str = "Training Curve", save_path: str = None) -> None:
    """
    Plot training and validation curves.
    
    Args:
        train_losses: List of training losses
        val_losses: List of validation losses (optional)
        train_acc: List of training accuracies (optional)
        val_acc: List of validation accuracies (optional)
        title: Title for the plot
        save_path: Path to save the plot (optional)
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle(title)
    
    # Plot losses
    ax1.plot(train_losses, label='Training Loss')
    if val_losses:
        ax1.plot(val_losses, label='Validation Loss')
    ax1.set_title('Loss')
    ax1.set_xlabel('Epoch')
    ax1.set_ylabel('Loss')
    ax1.legend()
    ax1.grid(True)
    
    # Plot accuracies
    if train_acc:
        ax2.plot(train_acc, label='Training Accuracy')
    if val_acc:
        ax2.plot(val_acc, label='Validation Accuracy')
    ax2.set_title('Accuracy')
    ax2.set_xlabel('Epoch')
    ax2.set_ylabel('Accuracy')
    ax2.legend()
    ax2.grid(True)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path)
        plt.close()
    else:
        plt.show()


def plot_federated_training(rounds: List[int], metrics: Dict[str, List[float]],
                          title: str = "Federated Training Progress",
                          save_path: str = None) -> None:
    """
    Plot federated training progress across rounds.
    
    Args:
        rounds: List of round numbers
        metrics: Dictionary of metric names to lists of values
        title: Title for the plot
        save_path: Path to save the plot (optional)
    """
    plt.figure(figsize=(10, 6))
    
    for metric_name, values in metrics.items():
        plt.plot(rounds, values, label=metric_name)
    
    plt.title(title)
    plt.xlabel('Communication Round')
    plt.ylabel('Metric Value')
    plt.legend()
    plt.grid(True)
    
    if save_path:
        plt.savefig(save_path)
        plt.close()
    else:
        plt.show()


def plot_privacy_utility_tradeoff(epsilon_values: List[float], accuracies: List[float],
                                title: str = "Privacy-Utility Tradeoff",
                                save_path: str = None) -> None:
    """
    Plot privacy-utility tradeoff curve.
    
    Args:
        epsilon_values: List of privacy budget (epsilon) values
        accuracies: List of corresponding model accuracies
        title: Title for the plot
        save_path: Path to save the plot (optional)
    """
    plt.figure(figsize=(8, 6))
    
    plt.plot(epsilon_values, accuracies, 'o-')
    plt.xscale('log')
    plt.title(title)
    plt.xlabel('Privacy Budget (ε)')
    plt.ylabel('Model Accuracy')
    plt.grid(True, which="both", ls="--")
    
    # Add annotations
    for i, (eps, acc) in enumerate(zip(epsilon_values, accuracies)):
        plt.annotate(f"{acc:.2f}", (eps, acc), textcoords="offset points", 
                    xytext=(0,10), ha='center')
    
    if save_path:
        plt.savefig(save_path)
        plt.close()
    else:
        plt.show()


def plot_client_distribution(client_sizes: List[int], title: str = "Client Data Distribution",
                           save_path: str = None) -> None:
    """
    Plot distribution of data across clients.
    
    Args:
        client_sizes: List of data sizes per client
        title: Title for the plot
        save_path: Path to save the plot (optional)
    """
    plt.figure(figsize=(10, 6))
    
    plt.bar(range(len(client_sizes)), client_sizes)
    plt.title(title)
    plt.xlabel('Client ID')
    plt.ylabel('Number of Samples')
    plt.grid(True, axis='y')
    
    if save_path:
        plt.savefig(save_path)
        plt.close()
    else:
        plt.show()


def plot_confusion_matrix(cm: np.ndarray, class_names: List[str] = None,
                         title: str = "Confusion Matrix",
                         save_path: str = None) -> None:
    """
    Plot confusion matrix.
    
    Args:
        cm: Confusion matrix as numpy array
        class_names: List of class names (optional)
        title: Title for the plot
        save_path: Path to save the plot (optional)
    """
    plt.figure(figsize=(8, 6))
    
    if class_names is None:
        class_names = [f"Class {i}" for i in range(cm.shape[0])]
    
    plt.imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
    plt.title(title)
    plt.colorbar()
    
    tick_marks = np.arange(len(class_names))
    plt.xticks(tick_marks, class_names, rotation=45)
    plt.yticks(tick_marks, class_names)
    
    # Add text annotations
    thresh = cm.max() / 2.
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            plt.text(j, i, format(cm[i, j], 'd'),
                    ha="center", va="center",
                    color="white" if cm[i, j] > thresh else "black")
    
    plt.tight_layout()
    plt.ylabel('True label')
    plt.xlabel('Predicted label')
    
    if save_path:
        plt.savefig(save_path)
        plt.close()
    else:
        plt.show()