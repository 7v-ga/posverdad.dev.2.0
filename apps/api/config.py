# apps/api/config.py

from pathlib import Path
from settings import settings  # importa la instancia global que ya tienes

BASE_DIR = Path(__file__).resolve().parents[2]  # raíz del repo, si lo necesitas

__all__ = ["settings", "BASE_DIR"]
