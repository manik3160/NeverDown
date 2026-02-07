from pathlib import Path
import os
from database.connection import get_settings

def check_paths():
    settings = get_settings()
    paths = {
        "WORKSPACE_DIR": settings.WORKSPACE_DIR,
        "SANITIZED_REPO_DIR": settings.SANITIZED_REPO_DIR,
        "CLONE_DIR": settings.CLONE_DIR
    }
    
    for name, p in paths.items():
        path = Path(p)
        print(f"{name}: {p}")
        print(f"Absolute: {path.absolute()}")
        try:
            path.mkdir(parents=True, exist_ok=True)
            test_file = path / "test.txt"
            test_file.write_text("test")
            print(f"Writable: Yes")
            test_file.unlink()
        except Exception as e:
            print(f"Writable: No ({e})")
        print("-" * 20)

if __name__ == "__main__":
    check_paths()
