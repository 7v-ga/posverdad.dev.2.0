# tests/conftest.py
from __future__ import annotations

import sys
from pathlib import Path
import pytest


def _repo_root_from_this_file(file: Path) -> Path:
    """
    Sube en el árbol hasta encontrar la carpeta 'tests' y devuelve su padre (la raíz del repo).
    Esto lo hace robusto aunque este conftest se mueva a tests/unit/ u otra subcarpeta.
    """
    p = file.resolve()
    # Busca 'tests' en la cadena de padres
    for ancestor in [p.parent] + list(p.parents):
        if ancestor.name == "tests":
            return ancestor.parent
    # Fallback: si no encuentra 'tests', asume el padre directo
    return p.parent


# --- Asegurar importación del paquete local ---
_REPO_ROOT = _repo_root_from_this_file(Path(__file__))
repo_str = str(_REPO_ROOT)
if repo_str not in sys.path:
    # Insertar al inicio para priorizar el código local sobre cualquier paquete instalado con el mismo nombre
    sys.path.insert(0, repo_str)


# --- Auto-marcado por estructura de carpetas ---
def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """
    Marca automáticamente los tests según su ubicación:
      tests/unit/...         -> mark 'unit'
      tests/integration/...  -> mark 'integration'
    """
    for item in items:
        path = Path(str(item.fspath)).resolve()
        # Busca el segmento 'tests' y mira el siguiente componente
        try:
            parts = path.parts
            idx = parts.index("tests")
            subdir = parts[idx + 1] if len(parts) > idx + 1 else ""
        except ValueError:
            subdir = ""

        if subdir == "unit":
            item.add_marker(pytest.mark.unit)
        elif subdir == "integration":
            item.add_marker(pytest.mark.integration)
