import functools
import warnings


def deprecated(replacement: str | None = None):
    """Decorator to mark functions as deprecated, emitting a warning on first use.

    Args:
        replacement: Optional string hinting at the new function to use.
    """
    def _wrap(func):
        warned = {"emitted": False}

        @functools.wraps(func)
        def _inner(*args, **kwargs):
            if not warned["emitted"]:
                msg = f"{func.__module__}.{func.__name__} is deprecated and will be removed."
                if replacement:
                    msg += f" Use {replacement} instead."
                warnings.warn(msg, category=DeprecationWarning, stacklevel=2)
                warned["emitted"] = True
            return func(*args, **kwargs)

        return _inner

    return _wrap


