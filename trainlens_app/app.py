import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import json
import os
import sys
import subprocess
import psutil
import time
import shutil
import random
from datetime import datetime
from pathlib import Path
from PIL import Image

# Page config
st.set_page_config(
    page_title="TrainLens Dashboard V1.5 Portable",
    page_icon="🚂",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Detect paths: APP_ROOT (TrainLens resources) and WORKSPACE_ROOT (user project)
def detect_paths():
    """
    Detect APP_ROOT and WORKSPACE_ROOT based on environment variables or runtime mode.

    APP_ROOT: TrainLens tool resources (trainlens_app, scripts, examples, docs, dataset)
    WORKSPACE_ROOT: User's CV project (train.py, dataset/, runs/, trainlens_config.json)
    """
    # Priority 1: Environment variables (set by trainlens_launcher.py)
    if os.getenv('TRAINLENS_APP_ROOT'):
        app_root = Path(os.getenv('TRAINLENS_APP_ROOT'))
    else:
        # Source mode: app.py is in trainlens_app/, so parent.parent is project root
        app_root = Path(__file__).resolve().parent.parent

    if os.getenv('TRAINLENS_WORKSPACE_ROOT'):
        workspace_root = Path(os.getenv('TRAINLENS_WORKSPACE_ROOT'))
    else:
        # Source mode: workspace = app root
        workspace_root = app_root

    return app_root, workspace_root

APP_ROOT, WORKSPACE_ROOT = detect_paths()

# Directories to skip when scanning for images
SKIP_DIRS = {'.venv', 'venv', '__pycache__', '.git', 'node_modules', 'build', 'dist', 'runs', 'annotations'}

# Config and runs are in WORKSPACE_ROOT (user project)
CONFIG_FILE = WORKSPACE_ROOT / "trainlens_config.json"
LOG_FILE = WORKSPACE_ROOT / "runs" / "current" / "metrics.jsonl"
RUNS_DIR = WORKSPACE_ROOT / "runs"

def resolve_default_python_interpreter(app_root, workspace_root):
    """
    Auto-detect Python interpreter for running user's training script.

    Priority:
    1. TRAINLENS_PYTHON environment variable
    2. WORKSPACE_ROOT/.venv/Scripts/python.exe
    3. WORKSPACE_ROOT/venv/Scripts/python.exe
    4. WORKSPACE_ROOT/env/Scripts/python.exe
    5. Source mode: APP_ROOT/.venv/Scripts/python.exe
    6. Non-frozen mode: sys.executable (running Python interpreter)
    7. shutil.which("python")
    8. shutil.which("py")

    Returns:
        str: Path to python interpreter, or None if not found
    """
    candidates = []

    # Priority 1: Environment variable
    if os.getenv('TRAINLENS_PYTHON'):
        candidates.append(os.getenv('TRAINLENS_PYTHON'))

    # Priority 2-4: WORKSPACE_ROOT virtual environments
    for venv_name in ['.venv', 'venv', 'env']:
        venv_python = workspace_root / venv_name / 'Scripts' / 'python.exe'
        if venv_python.exists():
            candidates.append(str(venv_python))

    # Priority 5: Source mode APP_ROOT/.venv
    if app_root == workspace_root:
        app_venv_python = app_root / '.venv' / 'Scripts' / 'python.exe'
        if app_venv_python.exists():
            candidates.append(str(app_venv_python))

    # Priority 6: Non-frozen mode, use current Python interpreter
    if not getattr(sys, 'frozen', False):
        candidates.append(sys.executable)

    # Priority 7-8: System PATH
    system_python = shutil.which("python")
    if system_python:
        candidates.append(system_python)

    py_launcher = shutil.which("py")
    if py_launcher:
        candidates.append(py_launcher)

    # Verify each candidate
    for candidate in candidates:
        try:
            result = subprocess.run(
                [candidate, '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return candidate
        except Exception:
            continue

    return None

def is_valid_python_interpreter(path: str) -> bool:
    """
    Verify if a Python interpreter path is valid and executable.

    Args:
        path: Path to python.exe

    Returns:
        bool: True if valid and executable, False otherwise
    """
    if not path:
        return False
    if not Path(path).exists():
        return False
    try:
        result = subprocess.run(
            [path, "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False

def find_system_python_for_venv():
    """
    Find system Python that can be used to create virtual environments.

    Returns:
        str: Path to system python, or None if not found
    """
    candidates = []

    # Don't use sys.executable in frozen mode (it's TrainLens.exe)
    if not getattr(sys, 'frozen', False):
        candidates.append(sys.executable)

    # Try common system Python commands
    for cmd in ["python", "py", "python3"]:
        python_path = shutil.which(cmd)
        if python_path:
            candidates.append(python_path)

    # Verify each candidate
    for candidate in candidates:
        if is_valid_python_interpreter(candidate):
            return candidate

    return None

def create_workspace_venv(workspace_root):
    """
    Create virtual environment in workspace root.

    Args:
        workspace_root: Path to workspace

    Returns:
        tuple: (success, message)
    """
    try:
        # Find system Python
        system_python = find_system_python_for_venv()
        if not system_python:
            return False, "System Python not found. Please install Python 3.10 or 3.11 and check 'Add Python to PATH'."

        venv_path = workspace_root / ".venv"

        # Create venv
        result = subprocess.run(
            [system_python, "-m", "venv", str(venv_path)],
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode != 0:
            return False, f"Failed to create venv: {result.stderr}"

        # Get venv python
        venv_python = venv_path / "Scripts" / "python.exe"
        if not venv_python.exists():
            return False, f"venv created but python.exe not found at {venv_python}"

        # Upgrade pip
        subprocess.run(
            [str(venv_python), "-m", "pip", "install", "--quiet", "--upgrade", "pip"],
            capture_output=True,
            timeout=60
        )

        # Install dependencies
        requirements_file = workspace_root / "requirements.txt"
        if requirements_file.exists():
            result = subprocess.run(
                [str(venv_python), "-m", "pip", "install", "-r", str(requirements_file)],
                capture_output=True,
                text=True,
                timeout=300
            )
            if result.returncode != 0:
                return True, f"venv created but requirements.txt installation failed: {result.stderr}\nYou can install manually later."
        else:
            # Install basic dependencies
            subprocess.run(
                [str(venv_python), "-m", "pip", "install", "--quiet", "numpy", "pillow"],
                capture_output=True,
                timeout=120
            )

        return True, f"Virtual environment created successfully at {venv_path}"

    except subprocess.TimeoutExpired:
        return False, "Operation timed out. Please try again or create venv manually."
    except Exception as e:
        return False, f"Error creating venv: {e}"

# Initialize session state
if 'training_process' not in st.session_state:
    st.session_state.training_process = None
if 'training_pid' not in st.session_state:
    st.session_state.training_pid = None
if 'last_command' not in st.session_state:
    st.session_state.last_command = None
if 'current_exp_dir' not in st.session_state:
    st.session_state.current_exp_dir = None
if 'exp_start_time' not in st.session_state:
    st.session_state.exp_start_time = None

# Helper functions
def get_next_exp_id():
    """Get next experiment ID by scanning runs/ directory"""
    RUNS_DIR.mkdir(parents=True, exist_ok=True)

    existing_exps = [d for d in RUNS_DIR.iterdir() if d.is_dir() and d.name.startswith('exp_')]

    if not existing_exps:
        return 1

    # Extract numbers from exp_xxx
    exp_nums = []
    for exp in existing_exps:
        try:
            num = int(exp.name.split('_')[1])
            exp_nums.append(num)
        except (IndexError, ValueError):
            continue

    return max(exp_nums) + 1 if exp_nums else 1

def create_exp_dir():
    """Create new experiment directory"""
    exp_id = get_next_exp_id()
    exp_name = f"exp_{exp_id:03d}"
    exp_dir = RUNS_DIR / exp_name
    exp_dir.mkdir(parents=True, exist_ok=True)
    return exp_dir

def save_exp_config(exp_dir, config, cmd):
    """Save experiment configuration"""
    exp_config = {
        'script_path': config['script_path'],
        'train_dir': config['train_dir'],
        'val_dir': config['val_dir'],
        'epochs': config['epochs'],
        'lr': config['lr'],
        'batch_size': config['batch_size'],
        'device': config['device'],
        'log_file': str(LOG_FILE),
        'start_time': datetime.now().isoformat(),
        'command': cmd
    }

    config_path = exp_dir / "config.json"
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(exp_config, f, indent=2)

def save_exp_summary(exp_dir, df, start_time):
    """Save experiment summary after training completes"""
    if df.empty:
        return

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    latest = df.iloc[-1]

    # Find best epoch
    best_acc_idx = df['acc'].idxmax()
    best_acc_row = df.loc[best_acc_idx]

    summary = {
        'status': 'completed',
        'start_time': start_time.isoformat(),
        'end_time': end_time.isoformat(),
        'duration_seconds': round(duration, 2),
        'total_epoch': int(latest.get('total_epoch', len(df))),
        'final_epoch': int(latest.get('epoch', len(df))),
        'final_acc': float(latest.get('acc', 0)),
        'final_loss': float(latest.get('val_loss', 0)),
        'best_acc': float(df['acc'].max()),
        'best_loss': float(df['val_loss'].min()),
        'best_epoch': int(best_acc_row.get('epoch', 0))
    }

    summary_path = exp_dir / "summary.json"
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)

def finalize_experiment(exp_dir):
    """Finalize experiment: copy metrics.jsonl and save summary"""
    try:
        # Copy metrics.jsonl
        if LOG_FILE.exists():
            shutil.copy2(LOG_FILE, exp_dir / "metrics.jsonl")

        # Read metrics and save summary
        df = read_metrics()
        if not df.empty and st.session_state.exp_start_time:
            save_exp_summary(exp_dir, df, st.session_state.exp_start_time)

        print(f"Experiment finalized: {exp_dir}")
    except Exception as e:
        print(f"Failed to finalize experiment: {e}")

def load_experiments():
    """Load all experiment history"""
    if not RUNS_DIR.exists():
        return pd.DataFrame()

    experiments = []

    for exp_dir in sorted(RUNS_DIR.iterdir()):
        if not exp_dir.is_dir() or not exp_dir.name.startswith('exp_'):
            continue

        summary_path = exp_dir / "summary.json"
        if not summary_path.exists():
            continue

        try:
            with open(summary_path, 'r', encoding='utf-8') as f:
                summary = json.load(f)

            summary['exp_id'] = exp_dir.name
            summary['exp_dir'] = str(exp_dir)
            experiments.append(summary)
        except Exception:
            continue

    if experiments:
        return pd.DataFrame(experiments)
    return pd.DataFrame()

def load_config():
    """Load saved configuration with Python interpreter validation"""
    saved_config = {}
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                saved_config = json.load(f)
        except Exception as e:
            st.error(f"Failed to load config: {e}")

    # Default configuration with smart path detection
    # Priority: WORKSPACE_ROOT/train.py > APP_ROOT/scripts/mock_train.py
    default_script = 'train.py'
    if not (WORKSPACE_ROOT / default_script).exists():
        default_script = str(APP_ROOT / 'scripts' / 'mock_train.py')

    # Priority: WORKSPACE_ROOT/dataset > APP_ROOT/dataset
    default_train_dir = str(WORKSPACE_ROOT / 'dataset' / 'train')
    if not Path(default_train_dir).exists():
        default_train_dir = str(APP_ROOT / 'dataset' / 'train')

    default_val_dir = str(WORKSPACE_ROOT / 'dataset' / 'val')
    if not Path(default_val_dir).exists():
        default_val_dir = str(APP_ROOT / 'dataset' / 'val')

    # Python interpreter: use saved if valid, otherwise auto-detect
    auto_python = resolve_default_python_interpreter(APP_ROOT, WORKSPACE_ROOT) or ''
    saved_python = saved_config.get('python_interpreter', '').strip()

    if is_valid_python_interpreter(saved_python):
        final_python = saved_python
    else:
        final_python = auto_python

    return {
        'script_path': saved_config.get('script_path', default_script),
        'train_dir': saved_config.get('train_dir', default_train_dir),
        'val_dir': saved_config.get('val_dir', default_val_dir),
        'epochs': saved_config.get('epochs', 20),
        'lr': saved_config.get('lr', 0.001),
        'batch_size': saved_config.get('batch_size', 16),
        'device': saved_config.get('device', 'auto'),
        'python_interpreter': final_python
    }

def save_config(config):
    """Save configuration to file"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        st.error(f"Failed to save config: {e}")

def is_training_running():
    """Check if training process is running"""
    if st.session_state.training_pid:
        try:
            process = psutil.Process(st.session_state.training_pid)
            return process.is_running()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            # Training finished, finalize experiment
            if st.session_state.current_exp_dir:
                finalize_experiment(Path(st.session_state.current_exp_dir))
                st.session_state.current_exp_dir = None
                st.session_state.exp_start_time = None

            st.session_state.training_pid = None
            st.session_state.training_process = None
    return False

def start_training(config):
    """Start training process"""
    try:
        # Validate Python interpreter
        python_interpreter = config.get('python_interpreter', '').strip()
        if not python_interpreter:
            return False, "Python interpreter not detected. Please check Advanced Settings."

        # Verify Python interpreter exists and is executable
        try:
            result = subprocess.run(
                [python_interpreter, '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                return False, f"Python interpreter is not valid: {python_interpreter}"
        except Exception as e:
            return False, f"Python interpreter is not executable: {python_interpreter}\n{e}"

        # Create experiment directory
        exp_dir = create_exp_dir()
        st.session_state.current_exp_dir = str(exp_dir)
        st.session_state.exp_start_time = datetime.now()

        # Clear old metrics file
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        LOG_FILE.write_text("", encoding="utf-8")

        # Build command - use detected Python interpreter
        script_path = WORKSPACE_ROOT / config['script_path']
        cmd = [
            python_interpreter,
            str(script_path),
            '--train', config['train_dir'],
            '--val', config['val_dir'],
            '--epochs', str(config['epochs']),
            '--lr', str(config['lr']),
            '--batch', str(config['batch_size']),
            '--device', config['device'],
            '--log', str(LOG_FILE)
        ]

        # Save experiment config
        cmd_str = ' '.join(cmd)
        save_exp_config(exp_dir, config, cmd_str)
        st.session_state.last_command = cmd_str

        # Open train.log for stdout/stderr
        train_log_path = exp_dir / "train.log"
        log_file = open(train_log_path, 'w', encoding='utf-8')

        # Start process
        process = subprocess.Popen(
            cmd,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            cwd=str(WORKSPACE_ROOT)
        )

        st.session_state.training_process = process
        st.session_state.training_pid = process.pid
        save_config(config)

        return True, f"Training started (PID: {process.pid}, Exp: {exp_dir.name})"
    except Exception as e:
        return False, f"Failed to start training: {e}"

def stop_training():
    """Stop training process"""
    if st.session_state.training_pid:
        try:
            process = psutil.Process(st.session_state.training_pid)
            process.terminate()
            process.wait(timeout=5)

            # Finalize experiment
            if st.session_state.current_exp_dir:
                finalize_experiment(Path(st.session_state.current_exp_dir))
                st.session_state.current_exp_dir = None
                st.session_state.exp_start_time = None

            st.session_state.training_pid = None
            st.session_state.training_process = None
            return True, "Training stopped"
        except psutil.TimeoutExpired:
            process.kill()
            if st.session_state.current_exp_dir:
                finalize_experiment(Path(st.session_state.current_exp_dir))
                st.session_state.current_exp_dir = None
                st.session_state.exp_start_time = None
            st.session_state.training_pid = None
            st.session_state.training_process = None
            return True, "Training force killed"
        except Exception as e:
            return False, f"Failed to stop training: {e}"
    return False, "No training process running"

def read_metrics():
    """Read metrics from JSONL file"""
    if not LOG_FILE.exists():
        return pd.DataFrame()

    try:
        lines = LOG_FILE.read_text(encoding="utf-8", errors="ignore").splitlines()
        rows = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                continue

        if rows:
            df = pd.DataFrame(rows)
            for col in ['epoch', 'total_epoch', 'progress', 'train_loss', 'val_loss', 'acc', 'best_acc', 'best_loss', 'lr']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Failed to read metrics: {e}")
        return pd.DataFrame()


# ============ Dataset Inspector Helpers ============

def scan_imagefolder_dataset(dataset_dir):
    """
    Scan ImageFolder format dataset directory.
    Returns dict: {class_name: [image_paths]}
    """
    dataset_path = Path(dataset_dir)
    if not dataset_path.exists():
        return {}

    class_dict = {}
    try:
        for class_dir in dataset_path.iterdir():
            if class_dir.is_dir():
                class_name = class_dir.name
                image_files = []
                for ext in ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.gif']:
                    image_files.extend(class_dir.glob(ext))
                    image_files.extend(class_dir.glob(ext.upper()))
                if image_files:
                    class_dict[class_name] = [str(f) for f in image_files]
    except Exception as e:
        st.error(f"Error scanning {dataset_dir}: {e}")

    return class_dict


def calculate_dataset_stats(train_dir, val_dir):
    """
    Calculate statistics for train and validation datasets.
    Returns dict with counts and imbalance ratio.
    """
    train_data = scan_imagefolder_dataset(train_dir)
    val_data = scan_imagefolder_dataset(val_dir)

    # Count images
    train_counts = {cls: len(paths) for cls, paths in train_data.items()}
    val_counts = {cls: len(paths) for cls, paths in val_data.items()}

    total_train = sum(train_counts.values())
    total_val = sum(val_counts.values())

    # Get all unique classes
    all_classes = sorted(set(train_counts.keys()) | set(val_counts.keys()))

    # Calculate imbalance ratio
    if train_counts:
        max_count = max(train_counts.values())
        min_count = min(train_counts.values())
        imbalance_ratio = max_count / min_count if min_count > 0 else float('inf')
    else:
        imbalance_ratio = 0.0

    return {
        'train_data': train_data,
        'val_data': val_data,
        'train_counts': train_counts,
        'val_counts': val_counts,
        'total_train': total_train,
        'total_val': total_val,
        'all_classes': all_classes,
        'imbalance_ratio': imbalance_ratio
    }


def get_random_images(image_paths, n=8):
    """Get random sample of image paths"""
    if len(image_paths) <= n:
        return image_paths
    return random.sample(image_paths, n)


# Main UI
st.title("🚂 TrainLens Dashboard V1.5 Portable")

# Sidebar - Configuration
with st.sidebar:
    st.header("⚙️ Training Configuration")

    config = load_config()

    script_path = st.text_input("Script Path", value=config['script_path'])
    train_dir = st.text_input("Train Directory", value=config['train_dir'])
    val_dir = st.text_input("Validation Directory", value=config['val_dir'])

    col1, col2 = st.columns(2)
    with col1:
        epochs = st.number_input("Epochs", min_value=1, max_value=1000, value=config['epochs'])
        batch_size = st.number_input("Batch Size", min_value=1, max_value=512, value=config['batch_size'])
    with col2:
        lr = st.number_input("Learning Rate", min_value=0.00001, max_value=1.0, value=config['lr'], format="%.5f")
        device = st.selectbox("Device", options=['auto', 'cpu', 'cuda'], index=['auto', 'cpu', 'cuda'].index(config['device']))

    st.divider()

    # Initialize or update Python interpreter in session state
    config_python = config.get('python_interpreter', '')

    # Initialize session state for Python interpreter if not exists
    if 'python_interpreter_input' not in st.session_state:
        st.session_state['python_interpreter_input'] = config_python
    # Update if current session state is invalid but config has valid path
    elif not is_valid_python_interpreter(st.session_state['python_interpreter_input']) and is_valid_python_interpreter(config_python):
        st.session_state['python_interpreter_input'] = config_python

    # Python Environment Display - show current state
    current_python = st.session_state.get('python_interpreter_input', '')
    if is_valid_python_interpreter(current_python):
        st.success("✓ Python Environment: Ready")
        st.caption(f"📍 {current_python}")
    else:
        st.error("⚠️ Python Environment: Not detected")
        st.caption("No project Python environment was detected.")
        st.caption("You can create a .venv for this project.")

        if st.button("🔧 Create .venv for this project", width="stretch"):
            with st.spinner("Creating virtual environment..."):
                success, message = create_workspace_venv(WORKSPACE_ROOT)

                if success:
                    st.success(message)
                    # Set new venv as Python interpreter
                    new_venv_python = str(WORKSPACE_ROOT / ".venv" / "Scripts" / "python.exe")
                    st.session_state['python_interpreter_input'] = new_venv_python
                    st.info("Reloading dashboard...")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(message)

    # Advanced Settings (collapsed by default)
    with st.expander("🔧 Advanced Settings", expanded=False):
        st.caption("Only modify these settings if auto-detection fails or you need to use a specific Python environment.")
        python_interpreter = st.text_input(
            "Python Interpreter",
            key="python_interpreter_input",
            help="Path to python.exe for running training scripts. Auto-detected by default.",
            placeholder="C:\\MyCVProject\\.venv\\Scripts\\python.exe"
        )
        if python_interpreter != config_python and python_interpreter:
            if is_valid_python_interpreter(python_interpreter):
                st.info("✓ Custom Python interpreter is valid and will be used.")
            else:
                st.warning("⚠️ Custom Python interpreter path may be invalid.")

    st.divider()

    # Control buttons
    is_running = is_training_running()

    if is_running:
        st.success(f"Training Running (PID: {st.session_state.training_pid})")
        if st.session_state.current_exp_dir:
            exp_name = Path(st.session_state.current_exp_dir).name
            st.info(f"Experiment: {exp_name}")
        if st.button("Stop Training", type="primary", width="stretch"):
            success, msg = stop_training()
            if success:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)
    else:
        st.info("Training Idle")
        if st.button("Start Training", type="primary", width="stretch"):
            # Use current Python interpreter from session state
            final_python = st.session_state.get('python_interpreter_input', '')

            new_config = {
                'script_path': script_path,
                'train_dir': train_dir,
                'val_dir': val_dir,
                'epochs': epochs,
                'lr': lr,
                'batch_size': batch_size,
                'device': device,
                'python_interpreter': final_python
            }
            success, msg = start_training(new_config)
            if success:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

    # Debug info
    st.divider()
    st.caption("Debug Info")
    st.caption(f"Next Exp ID: exp_{get_next_exp_id():03d}")
    st.caption(f"Current PID: {st.session_state.training_pid}")
    if st.session_state.current_exp_dir:
        st.caption(f"Current Exp: {Path(st.session_state.current_exp_dir).name}")

    # Protocol hint
    st.divider()
    st.info("💡 真实训练脚本需要遵守 TrainLens CLI + JSONL 协议")
    st.caption("详见: docs/TRAIN_SCRIPT_PROTOCOL.md")
    st.caption("示例: examples/example_cv_train.py")

# Show last command
if st.session_state.last_command:
    with st.expander("Last Training Command", expanded=False):
        st.code(st.session_state.last_command, language="bash")

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Current Training", "📜 Experiment History",
    "🔍 Dataset Inspector", "🏷️ Image Annotator", "🖼️ Browse Annotations"
])

with tab1:
    # Current training view
    df = read_metrics()

    if df.empty:
        st.info("No training data yet. Waiting for metrics.jsonl...")
    else:
        st.caption(f"Metrics: {len(df)} lines")

        latest = df.iloc[-1]
        progress = latest.get('progress', 0)
        if progress <= 1:
            progress *= 100

        epoch = int(latest.get('epoch', 0))
        total_epoch = int(latest.get('total_epoch', config['epochs']))

        # Progress wheel and metrics
        col_gauge, col_metrics = st.columns([1, 2])

        with col_gauge:
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=progress,
                number={"suffix": "%"},
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar": {"color": "#3b82f6"},
                },
                title={"text": f"Epoch {epoch} / {total_epoch}"}
            ))
            fig_gauge.update_layout(height=300, margin=dict(t=50, b=0, l=0, r=0))
            st.plotly_chart(fig_gauge, width="stretch")

        with col_metrics:
            col1, col2 = st.columns(2)
            with col1:
                acc = latest.get('acc', 0)
                best_acc = latest.get('best_acc', 0)
                st.metric("Current Acc", f"{acc:.2%}")
                st.metric("Best Acc", f"{best_acc:.2%}")
            with col2:
                val_loss = latest.get('val_loss', 0)
                best_loss = latest.get('best_loss', 0)
                st.metric("Current Loss", f"{val_loss:.4f}")
                st.metric("Best Loss", f"{best_loss:.4f}")

        st.divider()

        # Charts
        col_loss, col_acc = st.columns(2)

        with col_loss:
            st.subheader("Loss Curves")
            fig_loss = go.Figure()
            fig_loss.add_trace(go.Scatter(
                x=df['epoch'], y=df['train_loss'],
                mode='lines+markers',
                name='Train Loss',
                line=dict(color='#ef4444', width=2)
            ))
            fig_loss.add_trace(go.Scatter(
                x=df['epoch'], y=df['val_loss'],
                mode='lines+markers',
                name='Val Loss',
                line=dict(color='#3b82f6', width=2)
            ))
            if 'best_loss' in df.columns:
                fig_loss.add_trace(go.Scatter(
                    x=df['epoch'], y=df['best_loss'],
                    mode='lines',
                    name='Best Loss',
                    line=dict(color='#10b981', width=2, dash='dash')
                ))
            fig_loss.update_layout(height=350, xaxis_title="Epoch", yaxis_title="Loss", hovermode='x unified')
            st.plotly_chart(fig_loss, width="stretch")

        with col_acc:
            st.subheader("Accuracy Curves")
            fig_acc = go.Figure()
            fig_acc.add_trace(go.Scatter(
                x=df['epoch'], y=df['acc'] * 100,
                mode='lines+markers',
                name='Acc',
                line=dict(color='#ef4444', width=2)
            ))
            if 'best_acc' in df.columns:
                fig_acc.add_trace(go.Scatter(
                    x=df['epoch'], y=df['best_acc'] * 100,
                    mode='lines',
                    name='Best Acc',
                    line=dict(color='#10b981', width=2, dash='dash')
                ))
            fig_acc.update_layout(height=350, xaxis_title="Epoch", yaxis_title="Accuracy (%)", hovermode='x unified')
            st.plotly_chart(fig_acc, width="stretch")

        st.divider()

        # Data table
        st.subheader("Training History")
        display_df = df[['epoch', 'train_loss', 'val_loss', 'acc', 'best_acc', 'best_loss', 'progress']].copy()
        display_df['acc'] = display_df['acc'].apply(lambda x: f"{x:.2%}")
        display_df['best_acc'] = display_df['best_acc'].apply(lambda x: f"{x:.2%}")
        display_df['train_loss'] = display_df['train_loss'].apply(lambda x: f"{x:.4f}")
        display_df['val_loss'] = display_df['val_loss'].apply(lambda x: f"{x:.4f}")
        display_df['best_loss'] = display_df['best_loss'].apply(lambda x: f"{x:.4f}")
        display_df['progress'] = display_df['progress'].apply(lambda x: f"{x:.1f}%")
        st.dataframe(display_df, width="stretch", hide_index=True)

with tab2:
    # Experiment history
    st.subheader("📜 Experiment History")

    exp_df = load_experiments()

    if exp_df.empty:
        st.info("No completed experiments yet.")
    else:
        # Sort by start_time descending
        exp_df = exp_df.sort_values('start_time', ascending=False)

        # Format display
        display_exp = exp_df[[
            'exp_id', 'status', 'best_acc', 'best_loss',
            'final_acc', 'final_loss', 'total_epoch',
            'duration_seconds', 'start_time'
        ]].copy()

        display_exp['best_acc'] = display_exp['best_acc'].apply(lambda x: f"{x:.2%}")
        display_exp['best_loss'] = display_exp['best_loss'].apply(lambda x: f"{x:.4f}")
        display_exp['final_acc'] = display_exp['final_acc'].apply(lambda x: f"{x:.2%}")
        display_exp['final_loss'] = display_exp['final_loss'].apply(lambda x: f"{x:.4f}")
        display_exp['duration'] = display_exp['duration_seconds'].apply(lambda x: f"{x:.1f}s")
        display_exp['start_time'] = pd.to_datetime(display_exp['start_time']).dt.strftime('%Y-%m-%d %H:%M:%S')

        display_exp = display_exp.drop('duration_seconds', axis=1)

        st.dataframe(display_exp, width="stretch", hide_index=True)

        # Detail view
        st.divider()
        exp_ids = exp_df['exp_id'].tolist()
        selected_exp = st.selectbox("Select experiment to view details:", exp_ids)

        if selected_exp:
            exp_row = exp_df[exp_df['exp_id'] == selected_exp].iloc[0]
            exp_dir = Path(exp_row['exp_dir'])

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Experiment ID", selected_exp)
                st.metric("Status", exp_row['status'])
                st.metric("Total Epochs", exp_row['total_epoch'])
            with col2:
                st.metric("Best Acc", f"{exp_row['best_acc']:.2%}")
                st.metric("Final Acc", f"{exp_row['final_acc']:.2%}")
                st.metric("Best Epoch", exp_row['best_epoch'])
            with col3:
                st.metric("Best Loss", f"{exp_row['best_loss']:.4f}")
                st.metric("Final Loss", f"{exp_row['final_loss']:.4f}")
                st.metric("Duration", f"{exp_row['duration_seconds']:.1f}s")

            # Show config
            config_path = exp_dir / "config.json"
            if config_path.exists():
                with st.expander("Experiment Config", expanded=False):
                    with open(config_path, 'r') as f:
                        exp_config = json.load(f)
                    st.json(exp_config)

            # Show train.log tail
            train_log_path = exp_dir / "train.log"
            if train_log_path.exists():
                with st.expander("Training Log (last 50 lines)", expanded=False):
                    lines = train_log_path.read_text(encoding='utf-8', errors='ignore').splitlines()
                    st.code('\n'.join(lines[-50:]), language='text')

with tab3:
    # Dataset Inspector
    st.subheader("🔍 Dataset Inspector")

    st.info("自动读取侧边栏中的 Train Directory 和 Validation Directory，支持 ImageFolder 格式")

    # Refresh button
    if st.button("🔄 Refresh Dataset Stats"):
        st.rerun()

    # Use current train_dir and val_dir from sidebar
    current_train_dir = train_dir
    current_val_dir = val_dir

    st.caption(f"**Train Directory:** `{current_train_dir}`")
    st.caption(f"**Validation Directory:** `{current_val_dir}`")

    # Check if paths exist
    train_exists = Path(current_train_dir).exists()
    val_exists = Path(current_val_dir).exists()

    if not train_exists and not val_exists:
        st.warning("⚠️ Both Train and Validation directories do not exist. Please check your paths in the sidebar.")
    else:
        # Calculate statistics
        stats = calculate_dataset_stats(current_train_dir, current_val_dir)

        total_train = stats['total_train']
        total_val = stats['total_val']
        num_classes = len(stats['all_classes'])
        imbalance_ratio = stats['imbalance_ratio']

        # Summary metrics cards
        st.divider()
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Train Images", total_train)
        with col2:
            st.metric("Val Images", total_val)
        with col3:
            st.metric("Classes", num_classes)
        with col4:
            if imbalance_ratio == float('inf'):
                st.metric("Imbalance Ratio", "N/A")
            else:
                st.metric("Imbalance Ratio", f"{imbalance_ratio:.2f}")

        st.divider()

        if num_classes == 0:
            st.warning("⚠️ No valid ImageFolder structure detected. Expected format:\n```\ndataset/\n  train/\n    class1/\n      img1.jpg\n      img2.jpg\n    class2/\n      img1.jpg\n```")
        else:
            # Class distribution table
            st.subheader("Class Distribution")

            class_data = []
            for cls in stats['all_classes']:
                train_count = stats['train_counts'].get(cls, 0)
                val_count = stats['val_counts'].get(cls, 0)
                total_count = train_count + val_count
                class_data.append({
                    'Class': cls,
                    'Train': train_count,
                    'Val': val_count,
                    'Total': total_count
                })

            class_df = pd.DataFrame(class_data)
            st.dataframe(class_df, width="stretch", hide_index=True)

            st.divider()

            # Grouped bar chart
            st.subheader("Class Distribution Chart")

            fig_dist = go.Figure()
            fig_dist.add_trace(go.Bar(
                x=stats['all_classes'],
                y=[stats['train_counts'].get(cls, 0) for cls in stats['all_classes']],
                name='Train',
                marker_color='#3b82f6'
            ))
            fig_dist.add_trace(go.Bar(
                x=stats['all_classes'],
                y=[stats['val_counts'].get(cls, 0) for cls in stats['all_classes']],
                name='Val',
                marker_color='#ef4444'
            ))
            fig_dist.update_layout(
                barmode='group',
                xaxis_title='Class',
                yaxis_title='Number of Images',
                height=400,
                hovermode='x unified'
            )
            st.plotly_chart(fig_dist, width="stretch")

            st.divider()

            # Random image preview
            st.subheader("Random Training Image Samples")

            # Collect all training images
            all_train_images = []
            for cls, paths in stats['train_data'].items():
                all_train_images.extend(paths)

            if all_train_images:
                sample_images = get_random_images(all_train_images, n=8)

                # Display in 4x2 grid
                cols = st.columns(4)
                for idx, img_path in enumerate(sample_images):
                    with cols[idx % 4]:
                        try:
                            img = Image.open(img_path)
                            # Get class name from parent directory
                            class_name = Path(img_path).parent.name
                            st.image(img, caption=f"{class_name}", width="stretch")
                        except Exception as e:
                            st.error(f"Failed to load image: {e}")
            else:
                st.info("No training images found.")

with tab4:
    # Image Annotator
    st.subheader("🏷️ Image Annotator")

    st.info("Draw bounding boxes on images for object detection tasks. Annotations are saved in YOLO format.")

    # Annotation directory
    ANNOTATIONS_DIR = WORKSPACE_ROOT / "annotations"
    ANNOTATIONS_DIR.mkdir(exist_ok=True)

    # Class management
    CLASSES_FILE = ANNOTATIONS_DIR / "classes.txt"

    def load_classes():
        """Load class list from classes.txt"""
        if CLASSES_FILE.exists():
            return CLASSES_FILE.read_text(encoding='utf-8').strip().split('\n')
        return []

    def save_classes(classes):
        """Save class list to classes.txt"""
        CLASSES_FILE.write_text('\n'.join(classes), encoding='utf-8')

    def load_annotation(img_path):
        """Load YOLO format annotation for an image"""
        txt_path = ANNOTATIONS_DIR / (Path(img_path).stem + '.txt')
        if not txt_path.exists():
            return []

        annotations = []
        for line in txt_path.read_text(encoding='utf-8').strip().split('\n'):
            if line.strip():
                parts = line.split()
                if len(parts) == 5:
                    class_id, x_center, y_center, width, height = map(float, parts)
                    cid = int(class_id)
                    # Clamp class_id to valid range
                    if cid < 0:
                        cid = 0
                    if st.session_state.annotator_classes and cid >= len(st.session_state.annotator_classes):
                        cid = 0
                    annotations.append({
                        'class_id': cid,
                        'x_center': x_center,
                        'y_center': y_center,
                        'width': width,
                        'height': height
                    })
        return annotations

    def save_annotation(img_path, annotations):
        """Save annotations in YOLO format"""
        txt_path = ANNOTATIONS_DIR / (Path(img_path).stem + '.txt')

        if not annotations:
            # Remove annotation file if no annotations
            if txt_path.exists():
                txt_path.unlink()
            return

        lines = []
        for ann in annotations:
            lines.append(f"{ann['class_id']} {ann['x_center']:.6f} {ann['y_center']:.6f} {ann['width']:.6f} {ann['height']:.6f}")

        txt_path.write_text('\n'.join(lines), encoding='utf-8')

    # Color palette (shared across functions)
    COLORS_RGBA = [
        (239, 68, 68, 180),    # red
        (59, 130, 246, 180),   # blue
        (16, 185, 129, 180),   # green
        (245, 158, 11, 180),   # orange
        (139, 92, 246, 180),   # purple
        (236, 72, 153, 180),   # pink
        (20, 184, 166, 180),   # teal
        (249, 115, 22, 180)    # orange-red
    ]

    COLORS_HEX = ['#ef4444', '#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899', '#14b8a6', '#f97316']

    def draw_boxes_on_image(img, annotations, classes, target_annotations=None):
        """
        Draw bounding boxes on a PIL image.
        If target_annotations is provided (list of annotation dicts), only draw those specific boxes.
        Otherwise draw all annotations.
        Returns the modified image (drawn in-place).
        """
        from PIL import ImageDraw

        draw = ImageDraw.Draw(img, 'RGBA')
        img_width, img_height = img.size
        num_classes = len(classes) if classes else 1

        anns_to_draw = target_annotations if target_annotations is not None else annotations

        for ann in anns_to_draw:
            x_center = ann['x_center'] * img_width
            y_center = ann['y_center'] * img_height
            box_width = ann['width'] * img_width
            box_height = ann['height'] * img_height

            x0 = x_center - box_width / 2
            y0 = y_center - box_height / 2
            x1 = x_center + box_width / 2
            y1 = y_center + box_height / 2

            cid = int(ann.get('class_id', 0))
            if cid < 0 or cid >= num_classes:
                cid = 0
            class_name = classes[cid] if cid < len(classes) else f"cls_{cid}"
            color = COLORS_RGBA[cid % len(COLORS_RGBA)]

            # Draw rectangle
            draw.rectangle([x0, y0, x1, y1], outline=color, width=3)

            # Draw filled rectangle for label background
            label_text = f"{class_name}"
            label_bbox = draw.textbbox((0, 0), label_text)
            label_width = label_bbox[2] - label_bbox[0]
            label_height = label_bbox[3] - label_bbox[1]

            label_y = max(0, y0 - label_height - 6)
            draw.rectangle([x0, label_y, x0 + label_width + 8, label_y + label_height + 4], fill=color)
            draw.text((x0 + 4, label_y), label_text, fill=(255, 255, 255, 255))

        return img

    def generate_visualization(img_path, annotations, classes):
        """Generate visualization image with bounding boxes (all classes) and per-class gallery images"""
        try:
            # --- Load original image ---
            img_orig = Image.open(img_path).convert('RGB')
            ow, oh = img_orig.size

            # --- Smart upscale for good viewing (min 400px, max 800px) ---
            vis_scale = 1.0
            if ow < 400 or oh < 400:
                vis_scale = max(400 / ow, 400 / oh)
            if ow * vis_scale > 800:
                vis_scale = 800 / ow
            vw, vh = int(ow * vis_scale), int(oh * vis_scale)
            img_all = img_orig.resize((vw, vh), Image.Resampling.LANCZOS)
            # Scale annotations for the resized image
            scaled_annotations = []
            for a in annotations:
                scaled_annotations.append({
                    'class_id': a['class_id'],
                    'x_center': a['x_center'], 'y_center': a['y_center'],
                    'width': a['width'], 'height': a['height']
                })

            # --- Save combined visualization ---
            vis_dir = ANNOTATIONS_DIR / "visualizations"
            vis_dir.mkdir(exist_ok=True)
            vis_path = vis_dir / f"{Path(img_path).stem}_annotated.png"
            draw_boxes_on_image(img_all, scaled_annotations, classes)
            img_all.save(vis_path, 'PNG')

            # --- Save per-class gallery images ---
            gallery_dir = ANNOTATIONS_DIR / "gallery"
            # Clean upscaled base for gallery (no boxes yet)
            img_base = img_orig.resize((vw, vh), Image.Resampling.LANCZOS)

            class_annotations = {}
            for ann in annotations:
                cid = int(ann.get('class_id', 0))
                if cid < 0 or cid >= len(classes):
                    cid = 0
                class_name = classes[cid]
                if class_name not in class_annotations:
                    class_annotations[class_name] = []
                class_annotations[class_name].append(ann)

            for class_name, class_anns in class_annotations.items():
                img_per_class = img_base.copy()
                draw_boxes_on_image(img_per_class, scaled_annotations, classes, target_annotations=class_anns)

                class_gallery_dir = gallery_dir / class_name
                class_gallery_dir.mkdir(parents=True, exist_ok=True)
                class_vis_path = class_gallery_dir / f"{Path(img_path).stem}_annotated.png"
                img_per_class.save(class_vis_path, 'PNG')

            # Clean up any old JPEG visualizations to avoid confusion
            old_jpg = vis_dir / f"{Path(img_path).stem}_annotated.jpg"
            if old_jpg.exists():
                old_jpg.unlink()
            for cn in class_annotations:
                old_gj = gallery_dir / cn / f"{Path(img_path).stem}_annotated.jpg"
                if old_gj.exists():
                    old_gj.unlink()

            return True
        except Exception as e:
            st.error(f"Failed to generate visualization: {e}")
            return False

    # Initialize session state for annotator
    if 'annotator_classes' not in st.session_state:
        st.session_state.annotator_classes = load_classes()

    if 'annotator_current_image' not in st.session_state:
        st.session_state.annotator_current_image = None

    if 'annotator_annotations' not in st.session_state:
        st.session_state.annotator_annotations = []

    # Class management UI
    st.subheader("Class Management")

    col1, col2 = st.columns([3, 1])
    with col1:
        new_class_name = st.text_input("Add new class:", placeholder="e.g., person, car, dog")
    with col2:
        st.write("")
        st.write("")
        if st.button("➕ Add Class", width="stretch"):
            if new_class_name and new_class_name not in st.session_state.annotator_classes:
                st.session_state.annotator_classes.append(new_class_name)
                save_classes(st.session_state.annotator_classes)
                st.success(f"Added class: {new_class_name}")
                st.rerun()
            elif new_class_name in st.session_state.annotator_classes:
                st.warning("Class already exists!")

    if st.session_state.annotator_classes:
        st.caption(f"**Current classes ({len(st.session_state.annotator_classes)}):**")

        # Display classes with delete buttons
        class_cols = st.columns(min(len(st.session_state.annotator_classes), 4))
        for idx, cls in enumerate(st.session_state.annotator_classes):
            with class_cols[idx % 4]:
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.caption(f"`{idx}` - {cls}")
                with col_b:
                    if st.button("🗑️", key=f"del_class_{idx}"):
                        st.session_state.annotator_classes.pop(idx)
                        save_classes(st.session_state.annotator_classes)
                        st.rerun()
    else:
        st.warning("No classes defined yet. Add at least one class to start annotating.")

    st.divider()

    # Image selection
    st.subheader("Select Image to Annotate")

    # Collect all images (cached in session_state to avoid re-scanning)
    if 'cached_all_images' not in st.session_state:
        all_images = []
        train_path = Path(current_train_dir)
        val_path = Path(current_val_dir)
        seen = set()
        for root_path in [train_path, val_path, WORKSPACE_ROOT]:
            if root_path.exists():
                for img_path in root_path.rglob("*"):
                    if img_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.bmp', '.webp']:
                        if any(skip in img_path.parts for skip in SKIP_DIRS):
                            continue
                        key = f"{img_path.parent.name}/{img_path.name}"
                        if key not in seen:
                            seen.add(key)
                            all_images.append(str(img_path))
        st.session_state.cached_all_images = all_images
    else:
        all_images = st.session_state.cached_all_images

    if not all_images:
        st.warning("No images found in train or validation directories.")
    else:
        # Track current image index for fast A/D navigation
        if 'annotator_img_idx' not in st.session_state:
            st.session_state.annotator_img_idx = 0
        img_idx = st.session_state.annotator_img_idx
        if img_idx >= len(all_images):
            img_idx = 0
            st.session_state.annotator_img_idx = 0

        total_imgs = len(all_images)

        # Navigation: native HTML select (fully JS-controllable) + refresh
        nav_cols = st.columns([4, 0.5])
        with nav_cols[0]:
            # Build options HTML
            opts_html = ""
            for i, impath in enumerate(all_images):
                sel = " selected" if i == img_idx else ""
                label = f"{Path(impath).parent.name}/{Path(impath).name}"
                opts_html += f"<option value='{i}'{sel}>{label}</option>\n"
            st.markdown(
                f"<div style='display:flex;align-items:center;gap:6px'>"
                f"<span style='color:#888;font-size:13px'>📁</span>"
                f"<select id='annot_img_select' onchange='"
                f"var v=this.value;window.location.search=\"?jump=\"+v'"
                f" style='flex:1;padding:6px 8px;background:#1a1a2e;color:#ddd;"
                f"border:1px solid #444;border-radius:6px;font-size:14px'>"
                f"{opts_html}</select></div>",
                unsafe_allow_html=True
            )
        # Handle jump from native select
        qp = st.query_params
        if 'jump' in qp:
            try:
                ji = int(qp['jump'])
                if 0 <= ji < total_imgs:
                    st.session_state.annotator_img_idx = ji
                del qp['jump']
                st.rerun()
            except Exception:
                pass
        with nav_cols[1]:
            if st.button("🔄", key="refresh_imgs", help="Rescan images", use_container_width=True):
                st.session_state.cached_all_images = None
                st.rerun()

        # Sync current image from index
        current_img_path = all_images[img_idx] if img_idx < len(all_images) else all_images[0]
        if current_img_path != st.session_state.annotator_current_image:
            st.session_state.annotator_current_image = current_img_path
            st.session_state.annotator_annotations = load_annotation(current_img_path)
            st.rerun()

        # A/D keyboard navigation JS
        st.components.v1.html("""
        <script>
        (function(){
            var d=window.parent.document;
            function clickBtn(t){
                var bs=d.querySelectorAll('button');
                for(var i=0;i<bs.length;i++){
                    if(bs[i].textContent && bs[i].textContent.indexOf(t)>=0 &&
                       bs[i].offsetParent!==null){bs[i].click();return;}
                }
            }
            function hk(e){
                if(e.target.tagName==='INPUT'||e.target.tagName==='TEXTAREA') return;
                if(e.key==='a'||e.key==='A'){clickBtn('⬅️ A');e.preventDefault();}
                if(e.key==='d'||e.key==='D'){clickBtn('D ➡️');e.preventDefault();}
            }
            d.removeEventListener('keydown',hk);
            d.addEventListener('keydown',hk);
        })();
        </script>""", height=0)

        st.divider()

        # Annotation interface
        if st.session_state.annotator_current_image and st.session_state.annotator_classes:
            st.subheader("✏️ Draw Bounding Boxes")

            try:
                img = Image.open(st.session_state.annotator_current_image)
                img_width, img_height = img.size
                current_stem = Path(st.session_state.annotator_current_image).stem

                # JS-updated info bar (shows current image after A/D switch)
                st.markdown(
                    f"<div id='annot_img_info' style='"
                    f"background:#1a1a2e;padding:6px 12px;border-radius:6px;"
                    f"font-size:14px;color:#ccc;margin:4px 0;text-align:center;"
                    f"border:1px solid #333'><b style='color:#fff'>"
                    f"{Path(st.session_state.annotator_current_image).name}</b>"
                    f" &nbsp;|&nbsp; {img_idx+1}/{total_imgs}"
                    f" &nbsp;|&nbsp; {len(st.session_state.annotator_annotations)} boxes"
                    f" &nbsp;|&nbsp; ⌨️ <b>A</b> prev <b>D</b> next"
                    f"</div>",
                    unsafe_allow_html=True
                )

                # Select active class
                active_class = st.selectbox(
                    "Class:", st.session_state.annotator_classes,
                    key="active_draw_class", label_visibility="collapsed"
                )
                active_class_id = st.session_state.annotator_classes.index(active_class)
                active_color = COLORS_HEX[active_class_id % len(COLORS_HEX)]

                st.caption(f"✏️ **Drag on the image** (class: `{active_class}`) | ⌨️ **A** prev **D** next | **Delete** remove | **Right-click** undo")

                # --- Build pre-loaded image pack (fixed canvas 680×500, images centered) ---
                import io as _io, base64 as _b64, json as _json

                CANVAS_W, CANVAS_H = 680, 500  # fixed canvas size — never changes

                cache_key = f"img_pack_{total_imgs}"
                if cache_key not in st.session_state:
                    img_pack = []
                    for impath in all_images:
                        try:
                            pimg = Image.open(impath).convert('RGB')
                            ow, oh = pimg.size
                            # Scale to fit within fixed canvas
                            sc = min(CANVAS_W / ow, CANVAS_H / oh)
                            sc = min(sc, 6.0)  # max upscale 6x for tiny images
                            dw = int(ow * sc)
                            dh = int(oh * sc)
                            # Center offset
                            ox = (CANVAS_W - dw) // 2
                            oy = (CANVAS_H - dh) // 2
                            # Create canvas-sized image with black background + centered picture
                            canvas_img = Image.new('RGB', (CANVAS_W, CANVAS_H), (13, 13, 26))
                            pimg_resized = pimg.resize((dw, dh), Image.Resampling.LANCZOS)
                            canvas_img.paste(pimg_resized, (ox, oy))
                            buf = _io.BytesIO()
                            canvas_img.save(buf, format='PNG')
                            buf.seek(0)
                            data_url = f"data:image/png;base64,{_b64.b64encode(buf.read()).decode()}"
                            # Load annotations
                            anns = []
                            atxt = ANNOTATIONS_DIR / f"{Path(impath).stem}.txt"
                            if atxt.exists():
                                for line in atxt.read_text(encoding='utf-8').strip().split('\n'):
                                    parts = line.split()
                                    if len(parts) == 5:
                                        cid = int(float(parts[0]))
                                        if cid < 0: cid = 0
                                        if st.session_state.annotator_classes and cid >= len(st.session_state.annotator_classes): cid = 0
                                        anns.append({'class_id': cid, 'x_center': float(parts[1]), 'y_center': float(parts[2]), 'width': float(parts[3]), 'height': float(parts[4])})
                            img_pack.append({
                                'stem': Path(impath).stem,
                                'url': data_url,
                                'ow': ow, 'oh': oh,  # original dimensions for YOLO conversion
                                'dw': dw, 'dh': dh,  # display dimensions on canvas
                                'sc': sc, 'ox': ox, 'oy': oy,
                                'anns': anns
                            })
                        except Exception:
                            img_pack.append(None)
                    st.session_state[cache_key] = img_pack
                else:
                    img_pack = st.session_state[cache_key]

                all_classes_json = _json.dumps(st.session_state.annotator_classes)
                canvas_colors_json = _json.dumps(COLORS_HEX)
                img_pack_json = _json.dumps(img_pack)

                canvas_html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
body{{margin:0;background:#0d0d1a;text-align:center;font-family:sans-serif;}}
canvas{{display:inline-block;cursor:crosshair;}}
#bar{{color:#888;font-size:12px;padding:3px;}}
#bar span{{color:#ddd;font-weight:bold;}}
</style></head><body>
<canvas id="c" width="{CANVAS_W}" height="{CANVAS_H}"></canvas>
<div id="bar"><span id="status">Ready</span> &nbsp;|&nbsp; <span id="clsbadge">Class: <b style="color:{active_color}">{active_class}</b></span> &nbsp;|&nbsp; <span id="imgcounter"></span></div>
<script>
var IMGPACK={img_pack_json};
var TOTAL={total_imgs};
var CLASSES={all_classes_json};
var COLORS={canvas_colors_json};
var ACTIVE_CID={active_class_id};
var ACTIVE_COLOR='{active_color}';
var CW={CANVAS_W},CH={CANVAS_H};
var curIdx={img_idx};
var curPK=null;  // current image pack entry
var boxes=[];
var drawing=false,sx,sy,sel=-1;
var c=document.getElementById('c');
var ctx=c.getContext('2d');
var imgObj=new Image();

function loadImage(idx){{
    if(idx<0||idx>=TOTAL)return;
    curIdx=idx;
    var pk=IMGPACK[idx];
    if(!pk||!pk.url){{document.getElementById('status').textContent='No data';return;}}
    curPK=pk;
    var ni=new Image();
    ni.onload=function(){{
        imgObj=ni;
        // Convert normalized annotations to canvas pixel coords
        boxes=pk.anns.map(function(a){{
            var xc=a.x_center*CW, yc=a.y_center*CH;
            var bw=a.width*CW, bh=a.height*CH;
            return{{x:xc-bw/2,y:yc-bh/2,w:bw,h:bh,class_id:a.class_id}};
        }});
        redraw();send();
    }};
    ni.onerror=function(){{document.getElementById('status').textContent='Load failed';}};
    ni.src=pk.url;
    document.getElementById('imgcounter').textContent=(idx+1)+'/'+TOTAL;
    try{{
        var stem=pk.stem||'';
        var inf=window.parent.document.getElementById('annot_img_info');
        if(inf){{inf.innerHTML='<b style=\"color:#fff\">'+stem+'</b> &nbsp;|&nbsp; '+(idx+1)+'/'+TOTAL+' &nbsp;|&nbsp; '+boxes.length+' boxes &nbsp;|&nbsp; <b>A</b> prev <b>D</b> next';}}
        var sel=window.parent.document.getElementById('annot_img_select');
        if(sel){{sel.value=idx;}}
    }}catch(e){{}}
}}

function redraw(){{
ctx.clearRect(0,0,CW,CH);
ctx.drawImage(imgObj,0,0,CW,CH);
ctx.strokeStyle='rgba(128,128,128,0.12)';ctx.lineWidth=0.5;
for(let p=25;p<=75;p+=25){{
let gx=CW*p/100,gy=CH*p/100;
ctx.beginPath();ctx.moveTo(gx,0);ctx.lineTo(gx,CH);ctx.stroke();
ctx.beginPath();ctx.moveTo(0,gy);ctx.lineTo(CW,gy);ctx.stroke();
}}
boxes.forEach(function(b,i){{
let clr=COLORS[b.class_id%COLORS.length];
ctx.strokeStyle=clr;ctx.lineWidth=(i===sel)?4:2.5;
ctx.strokeRect(b.x,b.y,b.w,b.h);
let lb=CLASSES[b.class_id];if(!lb)lb='?';
ctx.font='bold 13px sans-serif';
let tm=ctx.measureText(lb),lw=tm.width+10,lh=20,ly=Math.max(0,b.y-lh-2);
ctx.fillStyle=clr;ctx.fillRect(b.x,ly,lw,lh);
ctx.fillStyle='#fff';ctx.fillText(lb,b.x+5,ly+15);
}});
}}

function hitTest(mx,my){{
for(let i=boxes.length-1;i>=0;i--){{
let b=boxes[i];
if(mx>=b.x&&mx<=b.x+b.w&&my>=b.y&&my<=b.y+b.h)return i;
}}
return -1;
}}

function send(){{
if(!curPK)return;
let r=boxes.map(function(b){{
return{{class_id:b.class_id,
x_center:(b.x+b.w/2)/CW,y_center:(b.y+b.h/2)/CH,
width:b.w/CW,height:b.h/CH}};
}});
let json=JSON.stringify({{stem:curPK.stem,boxes:r}});
try{{
var ta=window.parent.document.querySelectorAll('[data-testid="stTextArea"] textarea');
for(var i=0;i<ta.length;i++){{
var d=Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value');
d.set.call(ta[i],json);
ta[i].dispatchEvent(new Event('input',{{bubbles:true}}));
}}
}}catch(e){{}}
document.getElementById('status').textContent=boxes.length+' box(es) — click 💾 Save below';
}}

c.addEventListener('mousedown',function(e){{
let rc=c.getBoundingClientRect(),mx=e.clientX-rc.left,my=e.clientY-rc.top;
let h=hitTest(mx,my);
if(h>=0){{sel=h;redraw();return;}}
sel=-1;drawing=true;sx=mx;sy=my;redraw();
}});

c.addEventListener('mousemove',function(e){{
if(!drawing)return;
let rc=c.getBoundingClientRect(),mx=e.clientX-rc.left,my=e.clientY-rc.top;
redraw();
ctx.strokeStyle=ACTIVE_COLOR;ctx.lineWidth=2;ctx.setLineDash([6,4]);
ctx.strokeRect(sx,sy,mx-sx,my-sy);ctx.setLineDash([]);
}});

c.addEventListener('mouseup',function(e){{
if(!drawing){{drawing=false;return;}}
drawing=false;
let rc=c.getBoundingClientRect(),mx=e.clientX-rc.left,my=e.clientY-rc.top;
let x=Math.min(sx,mx),y=Math.min(sy,my),w=Math.abs(mx-sx),h=Math.abs(my-sy);
if(w<5||h<5){{redraw();send();return;}}
boxes.push({{x:x,y:y,w:w,h:h,class_id:ACTIVE_CID}});
redraw();send();
}});

document.addEventListener('keydown',function(e){{
if((e.key==='Delete'||e.key==='Backspace')&&sel>=0&&sel<boxes.length){{
boxes.splice(sel,1);sel=-1;redraw();send();
}}
if(e.target.tagName==='INPUT'||e.target.tagName==='TEXTAREA')return;
if(e.key==='a'||e.key==='A'){{if(curIdx>0)loadImage(curIdx-1);e.preventDefault();}}
if(e.key==='d'||e.key==='D'){{if(curIdx<TOTAL-1)loadImage(curIdx+1);e.preventDefault();}}
}});

c.addEventListener('contextmenu',function(e){{
e.preventDefault();
if(boxes.length>0){{boxes.pop();redraw();send();}}
}});

loadImage(curIdx);
</script></body></html>"""

                # Render canvas — iframe height fixed to match canvas
                st.components.v1.html(canvas_html, height=CANVAS_H + 60, scrolling=False)

                # --- Save via st.form (reads DOM value on submit, bypassing React) ---
                with st.form("save_form", clear_on_submit=False):
                    bridge_val = st.text_area(
                        "canvas_data", value="[]", key="canvas_data_bridge",
                        label_visibility="collapsed"
                    )
                    col_s, col_i = st.columns([1, 1])
                    with col_s:
                        submitted = st.form_submit_button("💾 Save Annotations", type="primary", use_container_width=True)
                    with col_i:
                        st.caption(f"📦 {len(st.session_state.annotator_annotations)} boxes on this image")

                if submitted:
                    try:
                        raw = bridge_val.strip() or "[]"
                        parsed = _json.loads(raw)
                        # New format: {{stem, boxes}}; Old format: [...]
                        if isinstance(parsed, dict):
                            stem = parsed.get('stem', '')
                            box_list = parsed.get('boxes', [])
                            # Find the actual image path from stem
                            target_img = None
                            if stem:
                                for impath in all_images:
                                    if Path(impath).stem == stem:
                                        target_img = impath
                                        break
                            if target_img:
                                st.session_state.annotator_current_image = target_img
                                st.session_state.annotator_img_idx = all_images.index(target_img) if target_img in all_images else st.session_state.annotator_img_idx
                        else:
                            box_list = parsed if isinstance(parsed, list) else []

                        if isinstance(box_list, list) and len(box_list) > 0:
                            new_annotations = []
                            for obj in box_list:
                                if isinstance(obj, dict):
                                    new_annotations.append({
                                        'class_id': int(obj.get('class_id', active_class_id)),
                                        'x_center': max(0, min(1, float(obj.get('x_center', 0)))),
                                        'y_center': max(0, min(1, float(obj.get('y_center', 0)))),
                                        'width': max(0.001, min(1, float(obj.get('width', 0.1)))),
                                        'height': max(0.001, min(1, float(obj.get('height', 0.1))))
                                    })
                            st.session_state.annotator_annotations = new_annotations
                            # Always save to current image (may have been corrected above)
                            save_annotation(st.session_state.annotator_current_image, new_annotations)
                            generate_visualization(st.session_state.annotator_current_image, new_annotations, st.session_state.annotator_classes)
                            # Invalidate img_pack cache so reload shows updated annotations
                            cache_key = f"img_pack_{total_imgs}"
                            if cache_key in st.session_state:
                                del st.session_state[cache_key]
                            st.success(f"✅ Saved {len(new_annotations)} boxes!")
                            st.rerun()
                        else:
                            st.warning("No boxes to save. Draw on the image first.")
                    except Exception:
                        st.error("Failed to parse canvas data.")

                # --- Manual Input (collapsed) ---
                with st.expander("🔧 Manual Input (Advanced)", expanded=False):
                    col1, col2 = st.columns(2)
                    with col1:
                        man_x = st.slider("X Center %", 0, 100, 50, 1, key="man_x")
                        man_y = st.slider("Y Center %", 0, 100, 50, 1, key="man_y")
                    with col2:
                        man_w = st.slider("Width %", 1, 100, 20, 1, key="man_w")
                        man_h = st.slider("Height %", 1, 100, 20, 1, key="man_h")
                    cm1, cm2 = st.columns([3, 1])
                    with cm1:
                        if st.button("✅ Add Manual Box", use_container_width=True):
                            st.session_state.annotator_annotations.append({
                                'class_id': active_class_id,
                                'x_center': man_x / 100.0, 'y_center': man_y / 100.0,
                                'width': man_w / 100.0, 'height': man_h / 100.0
                            })
                            save_annotation(st.session_state.annotator_current_image, st.session_state.annotator_annotations)
                            generate_visualization(st.session_state.annotator_current_image, st.session_state.annotator_annotations, st.session_state.annotator_classes)
                            st.success("Added!")
                            st.rerun()
                    with cm2:
                        if st.button("🗑️ Clear All", width="stretch"):
                            st.session_state.annotator_annotations = []
                            save_annotation(st.session_state.annotator_current_image, [])
                            vis_path = ANNOTATIONS_DIR / "visualizations" / f"{Path(st.session_state.annotator_current_image).stem}_annotated.png"
                            if vis_path.exists():
                                vis_path.unlink()
                            st.success("All cleared!")
                            st.rerun()

            except Exception as e:
                st.error(f"Canvas error: {e}")

            # --- Quick summary ---
            if st.session_state.annotator_annotations:
                cls_summary = {}
                for a in st.session_state.annotator_annotations:
                    cid = int(a.get('class_id', 0))
                    if cid < 0 or cid >= len(st.session_state.annotator_classes):
                        cid = 0
                    cn = st.session_state.annotator_classes[cid]
                    cls_summary[cn] = cls_summary.get(cn, 0) + 1
                parts = [f"`{c}`×{n}" for c, n in cls_summary.items()]
                st.caption(f"📦 {len(st.session_state.annotator_annotations)} boxes: {' | '.join(parts)}")

with tab5:
    # ============================================================
    # Browse Annotations — dedicated viewer + export + gallery
    # ============================================================
    st.subheader("🖼️ Browse Annotated Images")

    ANNOTATIONS_DIR_B = WORKSPACE_ROOT / "annotations"
    annotation_files = sorted(ANNOTATIONS_DIR_B.glob("*.txt"))

    if not annotation_files:
        st.info("No annotated images yet. Go to 🏷️ Image Annotator tab to start labeling.")
    else:
        # Build image list with metadata
        img_entries = []  # [{stem, path, boxes, classes: {name: count}, missing}]
        # Search roots: configured dirs + workspace root (fallback)
        search_roots = []
        for rp in [Path(current_train_dir), Path(current_val_dir)]:
            if rp.exists():
                search_roots.append(rp)
        # Also search workspace root (excluding venv, etc.)
        search_roots.append(WORKSPACE_ROOT)

        for txt_file in annotation_files:
            stem = txt_file.stem
            found_path = None
            for root_path in search_roots:
                for ext in ['.jpg', '.jpeg', '.png', '.bmp', '.webp']:
                    candidates = list(root_path.rglob(f"{stem}{ext}"))
                    if candidates:
                        # Prefer exact filename match, then any
                        exact = [c for c in candidates if c.stem == stem]
                        found_path = str(exact[0] if exact else candidates[0])
                        break
                if found_path:
                    break

            # Load annotations (works with or without image file)
            anns = []
            atxt = ANNOTATIONS_DIR_B / f"{stem}.txt"
            if atxt.exists():
                for line in atxt.read_text(encoding='utf-8').strip().split('\n'):
                    if line.strip():
                        parts = line.split()
                        if len(parts) == 5:
                            cid = int(float(parts[0]))
                            if cid < 0: cid = 0
                            if st.session_state.annotator_classes and cid >= len(st.session_state.annotator_classes):
                                cid = 0
                            anns.append({
                                'class_id': cid,
                                'x_center': float(parts[1]),
                                'y_center': float(parts[2]),
                                'width': float(parts[3]),
                                'height': float(parts[4])
                            })
            class_counts = {}
            for a in anns:
                cls_name = st.session_state.annotator_classes[a['class_id']] if a['class_id'] < len(st.session_state.annotator_classes) else f"cls_{a['class_id']}"
                class_counts[cls_name] = class_counts.get(cls_name, 0) + 1

            img_entries.append({
                'stem': stem,
                'path': found_path,
                'boxes': len(anns),
                'classes': class_counts,
                'annotations': anns,
                'missing': found_path is None
            })

        if not img_entries:
            st.warning("No annotation files found.")
        else:
            # Warn about missing images
            missing_count = sum(1 for e in img_entries if e['missing'])
            if missing_count > 0:
                st.warning(f"⚠️ {missing_count} annotation(s) have no matching image file. They will still appear in the list but cannot be previewed.")

            # Initialize session state for browser
            if 'browse_idx' not in st.session_state:
                st.session_state.browse_idx = 0

            total = len(img_entries)
            idx = st.session_state.browse_idx
            if idx >= total:
                idx = 0
                st.session_state.browse_idx = 0

            # --- Three-column layout ---
            left, center, right = st.columns([1.5, 4, 1.5])

            # === LEFT: Image list ===
            with left:
                st.caption(f"**📋 {total} annotated images**")
                # Quick nav slider (skip if only 1 image)
                if total > 1:
                    st.session_state.browse_idx = st.slider(
                        "Jump to", 0, total - 1, idx, 1,
                        key="browse_slider", label_visibility="collapsed"
                    )
                    idx = st.session_state.browse_idx

                # Native HTML list — click triggers JS bload, no Python rerun
                items_html = ""
                for i, e in enumerate(img_entries):
                    cls_str = ", ".join(f"{c}({n})" for c, n in e['classes'].items())
                    missing = " ⚠️" if e['missing'] else ""
                    sel_class = "browse-sel" if i == idx else ""
                    items_html += (
                        f"<div class='browse-item {sel_class}' onclick='bload({i})' "
                        f"style='padding:5px 8px;margin:2px 0;border-radius:5px;cursor:pointer;"
                        f"font-size:13px;color:#ccc;border:1px solid transparent;"
                        f"background:{'#1e1e3a' if i==idx else 'transparent'};"
                        f"border-color:{'#555' if i==idx else 'transparent'}'>"
                        f"<b>{e['stem']}</b> <span style='color:#888'>{e['boxes']}b</span>"
                        f"<span style='color:#666;font-size:11px'> {cls_str}</span>{missing}"
                        f"</div>"
                    )
                st.markdown(
                    f"<div style='max-height:60vh;overflow-y:auto' id='browse_list'>"
                    f"{items_html}</div>"
                    f"<style>.browse-item:hover{{background:#1a1a30;border-color:#444}}</style>",
                    unsafe_allow_html=True
                )

                # Click on list → calls bload_browse exposed by canvas iframe
                st.components.v1.html("""
                <script>
                window.bload = function(i) {
                    if (window.bload_browse) {
                        window.bload_browse(i);
                        var items = document.querySelectorAll('.browse-item');
                        for (var j = 0; j < items.length; j++) {
                            items[j].style.background = (j === i) ? '#1e1e3a' : 'transparent';
                            items[j].style.borderColor = (j === i) ? '#555' : 'transparent';
                        }
                    }
                };
                </script>""", height=0)

            # === CENTER: JS-powered preview (A/D instant, no rerun) ===
            with center:
                entry = img_entries[idx]
                st.caption(f"**{idx+1}/{total}** — `{entry['stem']}` | {entry['boxes']} boxes | ⌨️ **A** prev **D** next")

                # Build pre-loaded image pack
                browse_imgs = []
                for e in img_entries:
                    vp = ANNOTATIONS_DIR_B / "visualizations" / f"{e['stem']}_annotated.png"
                    url = ""; dw, dh = 400, 300
                    if vp.exists():
                        try:
                            pimg = Image.open(vp)
                            dw, dh = pimg.size
                            if dw > 550:
                                sc = 550 / dw
                                pimg = pimg.resize((550, int(dh * sc)), Image.Resampling.LANCZOS)
                                dw, dh = 550, int(dh * sc)
                            import io as _io_b, base64 as _b64_b
                            buf = _io_b.BytesIO(); pimg.save(buf, format='PNG'); buf.seek(0)
                            url = f"data:image/png;base64,{_b64_b.b64encode(buf.read()).decode()}"
                        except Exception: pass
                    browse_imgs.append({'stem': e['stem'], 'url': url, 'w': dw, 'h': dh, 'boxes': e['boxes']})
                import json as _json_b
                bjson = _json_b.dumps(browse_imgs)

                st.components.v1.html(f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
body{{margin:0;background:#0d0d1a;text-align:center;font-family:sans-serif;}}
canvas{{display:inline-block;border-radius:4px;max-width:100%;}}
#bstat{{color:#888;font-size:11px;padding:2px;}}
</style></head><body>
<canvas id="bc"></canvas><div id="bstat"></div>
<script>
var BIMGS={bjson};var BTOTAL={total};var bidx={idx};
var bc=document.getElementById('bc');var bctx=bc.getContext('2d');var bimg=new Image();
function bload(i){{
    if(i<0||i>=BTOTAL)return;bidx=i;var pk=BIMGS[i];
    bc.width=pk.w;bc.height=pk.h;
    if(!pk.url){{bctx.fillStyle='#333';bctx.fillRect(0,0,pk.w,pk.h);bctx.fillStyle='#888';bctx.font='14px sans-serif';bctx.fillText('No preview',pk.w/2-40,pk.h/2);}}
    else{{var ni=new Image();ni.onload=function(){{bimg=ni;bctx.drawImage(bimg,0,0,pk.w,pk.h);}};ni.src=pk.url;}}
    document.getElementById('bstat').textContent=(i+1)+'/'+BTOTAL+' — '+pk.stem+' | '+pk.boxes+' boxes';
    syncList(i);
}}
document.addEventListener('keydown',function(e){{
    if(e.target.tagName==='INPUT'||e.target.tagName==='TEXTAREA')return;
    if(e.key==='a'||e.key==='A'){{if(bidx>0)bload(bidx-1);e.preventDefault();}}
    if(e.key==='d'||e.key==='D'){{if(bidx<BTOTAL-1)bload(bidx+1);e.preventDefault();}}
}});
bload(bidx);
// Expose to parent for list clicks
try{{window.parent.bload_browse=bload;}}catch(e){{}}
// Highlight sync helper
function syncList(i){{
    try{{
        var items=window.parent.document.querySelectorAll('.browse-item');
        for(var j=0;j<items.length;j++){{
            items[j].style.background=(j===i)?'#1e1e3a':'transparent';
            items[j].style.borderColor=(j===i)?'#555':'transparent';
        }}
        window.parent.bload_last=i;
    }}catch(e){{}}
}}
syncList(bidx);
</script></body></html>""", height=600, scrolling=False)

                # Box details
                if entry['annotations']:
                    with st.expander("📦 Box Details", expanded=False):
                        for j, ann in enumerate(entry['annotations']):
                            cls_name = st.session_state.annotator_classes[ann['class_id']] if ann['class_id'] < len(st.session_state.annotator_classes) else f"cls_{ann['class_id']}"
                            color = COLORS_HEX[ann['class_id'] % len(COLORS_HEX)]
                            st.markdown(
                                f"<span style='background:{color};color:white;padding:1px 8px;border-radius:3px;font-size:12px'>{cls_name}</span> "
                                f"x={ann['x_center']*100:.0f}% y={ann['y_center']*100:.0f}% "
                                f"{ann['width']*100:.0f}%×{ann['height']*100:.0f}%",
                                unsafe_allow_html=True
                            )

            # === RIGHT: Class statistics ===
            with right:
                st.caption("**📊 Class Stats**")
                # Aggregate stats
                all_class_counts = {}
                for e in img_entries:
                    for cls_name, cnt in e['classes'].items():
                        all_class_counts[cls_name] = all_class_counts.get(cls_name, 0) + 1

                for cls_name, cnt in sorted(all_class_counts.items(), key=lambda x: -x[1]):
                    color = COLORS_HEX[st.session_state.annotator_classes.index(cls_name) % len(COLORS_HEX)] if cls_name in st.session_state.annotator_classes else "#888"
                    st.markdown(
                        f"<div style='margin:4px 0;padding:6px 10px;border-left:4px solid {color};"
                        f"background:rgba(255,255,255,0.03);border-radius:0 6px 6px 0'>"
                        f"<b>{cls_name}</b><br><span style='font-size:20px;font-weight:bold'>{cnt}</span> boxes"
                        f"</div>",
                        unsafe_allow_html=True
                    )

                st.divider()
                st.metric("Total Images", total)
                st.metric("Total Boxes", sum(e['boxes'] for e in img_entries))

                # Link back to annotator
                st.caption("💡 Switch to [🏷️ Image Annotator](#) tab to add/modify labels.")

        # --- Export Summary ---
        st.divider()
        st.subheader("📦 Export Summary")
        ec1, ec2, ec3 = st.columns(3)
        with ec1:
            st.metric("Annotated Images", total)
        with ec2:
            st.metric("Total Boxes", sum(e['boxes'] for e in img_entries))
        with ec3:
            vis_dir = ANNOTATIONS_DIR_B / "visualizations"
            vis_count = len(list(vis_dir.glob("*.jpg"))) + len(list(vis_dir.glob("*.png"))) if vis_dir.exists() else 0
            st.metric("Visualizations", vis_count)

        st.caption(f"📁 **Saved to:** `{ANNOTATIONS_DIR_B}`  |  **Format:** YOLO  |  **Classes:** `{CLASSES_FILE}`")

        col_gen, _ = st.columns([1, 2])
        with col_gen:
            if st.button("🖼️ Generate All Visualizations", use_container_width=True):
                with st.spinner("Generating..."):
                    ok = 0
                    for e in img_entries:
                        if generate_visualization(e['path'], e['annotations'], st.session_state.annotator_classes):
                            ok += 1
                st.success(f"Generated {ok} visualizations!")
                st.rerun()

        # --- Gallery ---
        st.divider()
        st.subheader("📊 Gallery — Browse by Class")

        if 'gallery_auto_done' not in st.session_state:
            st.session_state.gallery_auto_done = True
            missing = 0
            for e in img_entries:
                vp = ANNOTATIONS_DIR_B / "visualizations" / f"{e['stem']}_annotated.png"
                if not vp.exists():
                    generate_visualization(e['path'], e['annotations'], st.session_state.annotator_classes)
                    missing += 1
            if missing > 0:
                st.success(f"🖼️ Auto-generated {missing} visualizations!")

        gallery_dir = ANNOTATIONS_DIR_B / "gallery"
        if gallery_dir.exists():
            class_folders = [f for f in gallery_dir.iterdir() if f.is_dir()]
            if class_folders:
                selected_class = st.selectbox(
                    "Select class to view annotated images:",
                    options=[f.name for f in class_folders]
                )
                if selected_class:
                    class_dir = gallery_dir / selected_class
                    imgs = list(class_dir.glob("*.jpg")) + list(class_dir.glob("*.png"))
                    if imgs:
                        st.caption(f"**{selected_class}** — {len(imgs)} images")
                        cols = st.columns(3)
                        for i, ip in enumerate(imgs):
                            with cols[i % 3]:
                                st.image(str(ip), caption=ip.stem.replace('_annotated', ''))
                    else:
                        st.info(f"No images for class '{selected_class}'")
            else:
                st.warning("Gallery empty. Click **🖼️ Generate All Visualizations** above.")
        else:
            st.warning("No gallery folder yet. Save annotations and generate visualizations first.")

# Auto-refresh when training
if is_training_running():
    time.sleep(0.5)
    st.rerun()
