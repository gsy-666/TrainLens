import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import json
import os
import subprocess
import psutil
import time
from datetime import datetime
from pathlib import Path

# Page config
st.set_page_config(
    page_title="TrainLens Dashboard",
    page_icon="🚂",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = PROJECT_ROOT / "trainlens_config.json"
LOG_FILE = PROJECT_ROOT / "runs" / "current" / "metrics.jsonl"

# Initialize session state
if 'training_process' not in st.session_state:
    st.session_state.training_process = None
if 'training_pid' not in st.session_state:
    st.session_state.training_pid = None
if 'last_command' not in st.session_state:
    st.session_state.last_command = None

# Helper functions
def load_config():
    """Load saved configuration"""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Failed to load config: {e}")
    return {
        'script_path': 'scripts/mock_train.py',
        'train_dir': './dataset/train',
        'val_dir': './dataset/val',
        'epochs': 20,
        'lr': 0.001,
        'batch_size': 16,
        'device': 'auto'
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
            st.session_state.training_pid = None
            st.session_state.training_process = None
    return False

def start_training(config):
    """Start training process"""
    try:
        # Clear old metrics file
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        LOG_FILE.write_text("", encoding="utf-8")

        # Build command - match mock_train.py argument names
        script_path = PROJECT_ROOT / config['script_path']
        cmd = [
            'python',
            str(script_path),
            '--train', config['train_dir'],
            '--val', config['val_dir'],
            '--epochs', str(config['epochs']),
            '--lr', str(config['lr']),
            '--batch', str(config['batch_size']),
            '--device', config['device'],
            '--log', str(LOG_FILE)
        ]

        # Store command for display
        st.session_state.last_command = ' '.join(cmd)

        # Start process with PROJECT_ROOT as working directory
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            cwd=str(PROJECT_ROOT)
        )

        st.session_state.training_process = process
        st.session_state.training_pid = process.pid
        save_config(config)

        return True, f"Training started (PID: {process.pid})"
    except Exception as e:
        return False, f"Failed to start training: {e}"

def stop_training():
    """Stop training process"""
    if st.session_state.training_pid:
        try:
            process = psutil.Process(st.session_state.training_pid)
            process.terminate()
            process.wait(timeout=5)
            st.session_state.training_pid = None
            st.session_state.training_process = None
            return True, "Training stopped"
        except psutil.TimeoutExpired:
            process.kill()
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
            # Ensure numeric columns
            for col in ['epoch', 'total_epoch', 'progress', 'train_loss', 'val_loss', 'acc', 'best_acc', 'best_loss', 'lr']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Failed to read metrics: {e}")
        return pd.DataFrame()

# Main UI
st.title("🚂 TrainLens Dashboard")

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

    # Control buttons
    is_running = is_training_running()

    if is_running:
        st.success(f"Training Running (PID: {st.session_state.training_pid})")
        if st.button("Stop Training", type="primary", use_container_width=True):
            success, msg = stop_training()
            if success:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)
    else:
        st.info("Training Idle")
        if st.button("Start Training", type="primary", use_container_width=True):
            new_config = {
                'script_path': script_path,
                'train_dir': train_dir,
                'val_dir': val_dir,
                'epochs': epochs,
                'lr': lr,
                'batch_size': batch_size,
                'device': device
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
    st.caption(f"PROJECT_ROOT: {PROJECT_ROOT}")
    st.caption(f"LOG_FILE: {LOG_FILE}")
    st.caption(f"Log exists: {LOG_FILE.exists()}")
    if LOG_FILE.exists():
        st.caption(f"Log size: {LOG_FILE.stat().st_size} bytes")
    st.caption(f"Current PID: {st.session_state.training_pid}")

# Show last command
if st.session_state.last_command:
    with st.expander("Last Training Command", expanded=False):
        st.code(st.session_state.last_command, language="bash")

# Main content area
df = read_metrics()

if df.empty:
    st.info("No training data yet. Waiting for metrics.jsonl...")
    st.caption(f"Metrics count: 0 lines")
else:
    st.caption(f"Metrics count: {len(df)} lines")

    # Get latest metrics
    latest = df.iloc[-1]

    # Progress gauge
    progress = latest.get('progress', 0)
    if progress <= 1:
        progress *= 100

    epoch = int(latest.get('epoch', 0))
    total_epoch = int(latest.get('total_epoch', config['epochs']))

    # Progress wheel
    col_gauge, col_metrics = st.columns([1, 2])

    with col_gauge:
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=progress,
            number={"suffix": "%"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": "#3b82f6"},
                "steps": [
                    {"range": [0, 50], "color": "#e0e7ff"},
                    {"range": [50, 100], "color": "#c7d2fe"}
                ]
            },
            title={"text": f"Epoch {epoch} / {total_epoch}"}
        ))
        fig_gauge.update_layout(height=300, margin=dict(t=50, b=0, l=0, r=0))
        st.plotly_chart(fig_gauge, use_container_width=True)

    with col_metrics:
        # Metrics cards
        col1, col2 = st.columns(2)

        with col1:
            acc = latest.get('acc', 0)
            best_acc = latest.get('best_acc', 0)
            st.metric("Current Acc", f"{acc:.2%}", delta=None)
            st.metric("Best Acc", f"{best_acc:.2%}", delta=None)

        with col2:
            val_loss = latest.get('val_loss', 0)
            best_loss = latest.get('best_loss', 0)
            st.metric("Current Loss", f"{val_loss:.4f}", delta=None)
            st.metric("Best Loss", f"{best_loss:.4f}", delta=None)

    st.divider()

    # Charts - Accuracy and Loss curves
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
        fig_loss.update_layout(
            height=350,
            xaxis_title="Epoch",
            yaxis_title="Loss",
            hovermode='x unified'
        )
        st.plotly_chart(fig_loss, use_container_width=True)

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
        fig_acc.update_layout(
            height=350,
            xaxis_title="Epoch",
            yaxis_title="Accuracy (%)",
            hovermode='x unified'
        )
        st.plotly_chart(fig_acc, use_container_width=True)

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

    st.dataframe(display_df, use_container_width=True, hide_index=True)

# Auto-refresh when training - check every 500ms
if is_training_running():
    time.sleep(0.5)
    st.rerun()
