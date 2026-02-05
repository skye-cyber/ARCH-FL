import time
from functools import wraps
from typing import Callable, Any


def time_execution(func: Callable) -> Callable:
    """
    Decorator to measure and log the execution time of a function.

    Args:
        func: Function to be timed

    Returns:
        Wrapped function that measures execution time
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()

        execution_time = end_time - start_time
        print(f"⏱️  {func.__name__} executed in {execution_time:.4f} seconds")

        return result

    return wrapper


def log_execution(func: Callable) -> Callable:
    """
    Decorator to log function execution with arguments.

    Args:
        func: Function to be logged

    Returns:
        Wrapped function that logs execution
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        print(f"🚀 Executing {func.__name__} with args: {args}, kwargs: {kwargs}")
        result = func(*args, **kwargs)
        print(f"✅ Completed {func.__name__}")
        return result

    return wrapper


class Decorators:
    def __init__(self):
        pass

    @staticmethod
    def for_loop_decorator(data_list):
        """
        A decorator that calls the decorated function with each element
        from the provided list or tuple.

        Args:
            data_list: A list or tuple of data to iterate over.
        """

        def decorator(func):
            def wrapper(self, *args, **kwargs):
                for item in data_list:
                    func(self, item, *args, **kwargs)

            return wrapper

        return decorator
