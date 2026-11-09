"""EnvSieve: Zero-dependency environment variable & template drift detection."""

__version__ = "0.1.0"
__all__ = ["analyze_env_drift", "EnvSieveAuditor", "EnvSieveReport"]

from .core import EnvSieveAuditor, EnvSieveReport, analyze_env_drift
