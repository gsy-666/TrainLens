#!/usr/bin/env python3
"""
TrainLens Launcher
Entry point for PyInstaller packaged executable
"""
import os
import sys
from pathlib import Path


def detect_paths():
    """
    Detect APP_ROOT and WORKSPACE_ROOT based on runtime environment.

    APP_ROOT: Directory containing TrainLens resources (trainlens_app, scripts, docs, dataset)
              In EXE mode, may be in _internal or same level as exe
    WORKSPACE_ROOT: User's CV project directory (train.py, dataset/, runs/)
                    In EXE mode, parent of TrainLens folder

    Returns:
        tuple: (app_root, workspace_root) as Path objects
    """
    # Check for environment variable overrides first
    if os.getenv('TRAINLENS_APP_ROOT'):
        app_root = Path(os.getenv('TRAINLENS_APP_ROOT'))
    elif getattr(sys, 'frozen', False):
        # Running as PyInstaller executable
        exe_dir = Path(sys.executable).parent

        # Check for resources in multiple locations
        # Priority 1: exe_dir/trainlens_app (onedir mode with data at top level)
        # Priority 2: _MEIPASS/trainlens_app (resources in temp extraction dir)
        candidate_paths = [
            exe_dir / "trainlens_app",
            Path(getattr(sys, '_MEIPASS', exe_dir)) / "trainlens_app"
        ]

        app_root = None
        for candidate in candidate_paths:
            if candidate.exists() and (candidate / "app.py").exists():
                app_root = candidate.parent
                break

        if not app_root:
            # Fallback to exe_dir if detection fails
            app_root = exe_dir
    else:
        # Running from source
        app_root = Path(__file__).resolve().parent

    if os.getenv('TRAINLENS_WORKSPACE_ROOT'):
        workspace_root = Path(os.getenv('TRAINLENS_WORKSPACE_ROOT'))
    elif getattr(sys, 'frozen', False):
        # In EXE mode: workspace is parent of TrainLens folder
        # Structure: MyCVProject/TrainLens/TrainLens.exe
        # So workspace = TrainLens.exe parent's parent
        workspace_root = Path(sys.executable).parent.parent
    else:
        # In source mode: workspace = app root
        workspace_root = app_root

    return app_root, workspace_root


def main():
    """Launch Streamlit Dashboard"""
    # Detect paths
    app_root, workspace_root = detect_paths()

    # Set environment variables for app.py to use
    os.environ['TRAINLENS_APP_ROOT'] = str(app_root)
    os.environ['TRAINLENS_WORKSPACE_ROOT'] = str(workspace_root)

    # Verify app.py exists
    app_path = app_root / 'trainlens_app' / 'app.py'
    if not app_path.exists():
        print(f"ERROR: Dashboard not found at {app_path}")
        print(f"APP_ROOT: {app_root}")
        print(f"WORKSPACE_ROOT: {workspace_root}")
        input("Press Enter to exit...")
        sys.exit(1)

    print("=" * 60)
    print("TrainLens Dashboard")
    print("=" * 60)
    print(f"APP_ROOT: {app_root}")
    print(f"WORKSPACE_ROOT: {workspace_root}")
    print(f"Dashboard: {app_path}")
    print()
    print("Starting Streamlit...")
    print("Browser will open at http://localhost:8501")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    print()

    # Launch Streamlit
    try:
        from streamlit.web import cli as stcli

        # Disable development mode for EXE
        os.environ["STREAMLIT_GLOBAL_DEVELOPMENT_MODE"] = "false"
        os.environ["STREAMLIT_SERVER_HEADLESS"] = "false"
        os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"

        sys.argv = [
            "streamlit",
            "run",
            str(app_path),
            "--global.developmentMode=false",
            "--server.port=8501",
            "--server.headless=false",
            "--browser.gatherUsageStats=false"
        ]

        stcli.main()
    except KeyboardInterrupt:
        print("\nTrainLens stopped")
        sys.exit(0)
    except Exception as e:
        print(f"\nERROR: Failed to start TrainLens")
        print(f"{e}")
        input("Press Enter to exit...")
        sys.exit(1)


if __name__ == '__main__':
    main()
