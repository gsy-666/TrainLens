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
        st.caption("Please configure Python interpreter in Advanced Settings below.")

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

# Tabs for Current Training, Experiment History, and Dataset Inspector
tab1, tab2, tab3 = st.tabs(["📊 Current Training", "📜 Experiment History", "🔍 Dataset Inspector"])

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

# Auto-refresh when training
if is_training_running():
    time.sleep(0.5)
    st.rerun()
