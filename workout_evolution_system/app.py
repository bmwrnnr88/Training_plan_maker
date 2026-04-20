from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


def _load_v2_app_main():
    """Load the replacement Streamlit app from the v2 planner workspace."""
    project_root = Path(__file__).resolve().parent.parent
    v2_dir = project_root / "v2" / "training_planner"
    v2_app_path = v2_dir / "app.py"

    if str(v2_dir) not in sys.path:
        sys.path.insert(0, str(v2_dir))

    spec = importlib.util.spec_from_file_location("training_planner_v2_app", v2_app_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load v2 app from {v2_app_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.main


main = _load_v2_app_main()


if __name__ == "__main__":
    main()
