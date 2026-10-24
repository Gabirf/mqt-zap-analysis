import importlib.util
import shutil
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent

# 1. Ensure .venv site-packages has the required python files from QMAP without shadowing .so binaries
qmap_source_dir = WORKSPACE_ROOT / "QMAP" / "python" / "mqt" / "qmap"
site_packages_dir = WORKSPACE_ROOT / ".venv" / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages" / "mqt" / "qmap"

if site_packages_dir.exists() and qmap_source_dir.exists():
    if not (site_packages_dir / "_qdmi_paths.py").exists():
        for py_file in qmap_source_dir.glob("*.py"):
            try:
                shutil.copy(py_file, site_packages_dir)
            except Exception:
                pass

# 2. Pre-load _qdmi_paths into sys.modules so C++ na.abi3.so can find it immediately
if "mqt.qmap._qdmi_paths" not in sys.modules:
    qdmi_file = (site_packages_dir / "_qdmi_paths.py") if (site_packages_dir / "_qdmi_paths.py").exists() else (qmap_source_dir / "_qdmi_paths.py")
    if qdmi_file.exists():
        spec = importlib.util.spec_from_file_location("mqt.qmap._qdmi_paths", qdmi_file)
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            sys.modules["mqt.qmap._qdmi_paths"] = mod
            spec.loader.exec_module(mod)

ZAP_OUTPUT = WORKSPACE_ROOT / "output" / "ZAP"
QMAP_OUTPUT = WORKSPACE_ROOT / "output" / "QMAP"
CIRCUIT_INPUT = WORKSPACE_ROOT / "input" / "circuits"
ARCH_INPUT = WORKSPACE_ROOT / "input" / "arch"

FIDEL_Q1 = 0.9997
FIDEL_Q2 = 0.995
FIDEL_CROSS = 0.9975
FIDEL_TRAN = 0.999
FIDEL_TALK = 0.9975
ACC = 2.75

t_1 = 1.0
t_2 = 0.2
t_t = 15.0
