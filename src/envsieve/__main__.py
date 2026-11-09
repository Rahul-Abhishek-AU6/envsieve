"""Entrypoint for python -m envsieve."""
import sys
from .cli import main

if __name__ == "__main__":
    sys.exit(main())
