import importlib.util
from pathlib import Path


def load_app_module():
    module_path = Path(__file__).with_name("app.py")
    spec = importlib.util.spec_from_file_location("adaptive_traffic_app", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


if __name__ == "__main__":
    app = load_app_module()
    app.main()
