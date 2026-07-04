import * as crypto from 'crypto';
import * as fs from 'fs';
import * as path from 'path';
import { spawn, ChildProcessWithoutNullStreams } from 'child_process';
import * as vscode from 'vscode';

interface TrainFormState {
  scriptPath: string;
  trainDir: string;
  valDir: string;
  epochs: string;
  lr: string;
  batch: string;
  device: string;
}

interface MetricsRecord {
  epoch?: number;
  total_epoch?: number;
  progress?: number;
  train_loss?: number;
  val_loss?: number;
  acc?: number;
  best_acc?: number;
  best_loss?: number;
  lr?: number;
  device?: string;
  [key: string]: unknown;
}

interface LogEntry {
  level: 'system' | 'stdout' | 'stderr' | 'error';
  text: string;
}

type RuntimeStatus = 'idle' | 'starting' | 'running' | 'stopping' | 'error';

type WebviewToExtensionMessage =
  | { type: 'ready' }
  | { type: 'start'; state: TrainFormState }
  | { type: 'stop' }
  | { type: 'stateChanged'; state: TrainFormState };

const DEFAULT_FORM_STATE: TrainFormState = {
  scriptPath: 'scripts/mock_train.py',
  trainDir: './dataset/train',
  valDir: './dataset/val',
  epochs: '20',
  lr: '0.001',
  batch: '16',
  device: 'auto',
};

const MAX_LOG_LINES = 400;
const MAX_CHART_POINTS = 200;
const METRICS_RELATIVE_PATH = path.join('runs', 'current', 'metrics.jsonl');

function getNonce(): string {
  return crypto.randomBytes(16).toString('base64');
}

function safeJson(value: unknown): string {
  return JSON.stringify(value)
    .replace(/</g, '\\u003c')
    .replace(/>/g, '\\u003e')
    .replace(/&/g, '\\u0026');
}

function isFiniteNumber(value: unknown): value is number {
  return typeof value === 'number' && Number.isFinite(value);
}

function formatMetric(value: unknown, digits = 4): string {
  return isFiniteNumber(value) ? value.toFixed(digits) : '-';
}

function formatEpochValue(value: unknown): string {
  return isFiniteNumber(value) ? String(Math.round(value)) : '--';
}

function quoteForPreview(value: string): string {
  if (!/[\s"'`\\]/.test(value)) {
    return value;
  }
  return '"' + value.replace(/\\/g, '\\\\').replace(/"/g, '\\"') + '"';
}

function resolveWorkspacePath(root: string, input: string): string {
  return path.isAbsolute(input) ? input : path.resolve(root, input);
}

function parsePositiveInteger(input: string): number | null {
  const parsed = Number.parseInt(input, 10);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : null;
}

function parsePositiveNumber(input: string): number | null {
  const parsed = Number.parseFloat(input);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : null;
}

function buildCommandPreview(state: TrainFormState): string {
  return [
    'python',
    state.scriptPath.trim(),
    '--train',
    state.trainDir.trim(),
    '--val',
    state.valDir.trim(),
    '--epochs',
    state.epochs.trim(),
    '--lr',
    state.lr.trim(),
    '--batch',
    state.batch.trim(),
    '--device',
    state.device.trim(),
    '--log',
    METRICS_RELATIVE_PATH,
  ]
    .map(quoteForPreview)
    .join(' ');
}

function buildSpawnArgs(state: TrainFormState): string[] {
  return [
    state.scriptPath.trim(),
    '--train',
    state.trainDir.trim(),
    '--val',
    state.valDir.trim(),
    '--epochs',
    state.epochs.trim(),
    '--lr',
    state.lr.trim(),
    '--batch',
    state.batch.trim(),
    '--device',
    state.device.trim(),
    '--log',
    METRICS_RELATIVE_PATH,
  ];
}

function parseMetricsHistory(raw: string): MetricsRecord[] {
  const history: MetricsRecord[] = [];
  for (const line of raw.split(/\r?\n/)) {
    const trimmed = line.trim();
    if (!trimmed) {
      continue;
    }
    try {
      const parsed: unknown = JSON.parse(trimmed);
      if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
        history.push(parsed as MetricsRecord);
      }
    } catch {
      // Skip malformed lines.
    }
  }
  return history;
}

function currentMetricsFromHistory(history: MetricsRecord[]): MetricsRecord | null {
  return history.length > 0 ? history[history.length - 1] : null;
}

function runtimeStatusLabel(status: RuntimeStatus): string {
  switch (status) {
    case 'idle':
      return 'Idle';
    case 'starting':
      return 'Starting';
    case 'running':
      return 'Running';
    case 'stopping':
      return 'Stopping';
    case 'error':
      return 'Error';
    default:
      return 'Idle';
  }
}

class TrainLensController implements vscode.Disposable {
  private panel: vscode.WebviewPanel | undefined;
  private webviewReady = false;
  private workspaceRoot: string | undefined;
  private metricsFilePath: string | undefined;
  private metricsWatcher: ((curr: fs.Stats, prev: fs.Stats) => void) | undefined;
  private process: ChildProcessWithoutNullStreams | undefined;
  private stdoutBuffer = '';
  private stderrBuffer = '';
  private stopRequested = false;
  private disposed = false;
  private currentFormState: TrainFormState = { ...DEFAULT_FORM_STATE };
  private status: RuntimeStatus = 'idle';
  private logs: LogEntry[] = [];
  private metricsHistory: MetricsRecord[] = [];

  constructor() {}

  public dispose(): void {
    this.disposed = true;
    this.stopMetricsWatcher();
    this.terminateProcess();
    this.panel?.dispose();
    this.panel = undefined;
  }

  public async openDashboard(): Promise<void> {
    console.log('TrainLens openDashboard called');
    const workspaceRoot = this.getWorkspaceRoot();
    if (!workspaceRoot) {
      console.log('TrainLens: No workspace folder open, using default path');
      // 如果没有工作区，使用插件所在目录作为默认路径
      this.workspaceRoot = 'C:\\Users\\gsy_666\\Desktop\\TrainLens';
    } else {
      console.log('TrainLens workspace root:', workspaceRoot);
      this.workspaceRoot = workspaceRoot;
    }

    this.ensureMetricsWatcher(this.workspaceRoot);

    if (this.panel) {
      console.log('TrainLens: Panel already exists, revealing it');
      this.panel.reveal(vscode.ViewColumn.One);
      return;
    }

    console.log('TrainLens: Creating new webview panel');
    const panel = vscode.window.createWebviewPanel(
      'trainLensDashboard',
      'TrainLens',
      vscode.ViewColumn.One,
      {
        enableScripts: true,
        retainContextWhenHidden: true,
      },
    );

    this.panel = panel;
    this.webviewReady = false;
    panel.webview.html = this.renderHtml(panel.webview);
    console.log('TrainLens: Webview panel created successfully');

    panel.webview.onDidReceiveMessage((message: WebviewToExtensionMessage) => {
      console.log('TrainLens received message from webview:', message.type);
      void this.handleWebviewMessage(message);
    });

    panel.onDidDispose(() => {
      console.log('TrainLens: Webview panel disposed');
      this.panel = undefined;
      this.webviewReady = false;
    });
  }

  private async handleWebviewMessage(message: WebviewToExtensionMessage): Promise<void> {
    console.log('TrainLens handleWebviewMessage:', message.type);
    switch (message.type) {
      case 'ready':
        console.log('TrainLens: Webview ready');
        this.webviewReady = true;
        this.sendSnapshot();
        return;
      case 'stateChanged':
        this.currentFormState = message.state;
        return;
      case 'start':
        console.log('TrainLens: Start training requested');
        this.currentFormState = message.state;
        await this.startTraining(message.state);
        return;
      case 'stop':
        console.log('TrainLens: Stop training requested');
        await this.stopTraining();
        return;
      default:
        return;
    }
  }

  private getWorkspaceRoot(): string | undefined {
    return vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
  }

  private ensureMetricsWatcher(workspaceRoot: string): void {
    const nextMetricsPath = path.join(workspaceRoot, 'runs', 'current', 'metrics.jsonl');
    if (this.metricsFilePath !== nextMetricsPath) {
      this.stopMetricsWatcher();
      this.metricsFilePath = nextMetricsPath;
      this.metricsWatcher = () => {
        void this.refreshMetricsFromDisk();
      };
      fs.watchFile(this.metricsFilePath, { interval: 500 }, this.metricsWatcher);
    }
    void this.refreshMetricsFromDisk();
  }

  private stopMetricsWatcher(): void {
    if (this.metricsFilePath && this.metricsWatcher) {
      fs.unwatchFile(this.metricsFilePath, this.metricsWatcher);
    }
    this.metricsWatcher = undefined;
  }

  private async refreshMetricsFromDisk(): Promise<void> {
    if (!this.metricsFilePath) {
      return;
    }

    let raw = '';
    try {
      raw = await fs.promises.readFile(this.metricsFilePath, 'utf8');
    } catch (error) {
      const code = typeof error === 'object' && error && 'code' in error ? (error as NodeJS.ErrnoException).code : undefined;
      if (code === 'ENOENT') {
        this.updateMetricsHistory([]);
      }
      return;
    }

    const nextHistory = parseMetricsHistory(raw);
    this.updateMetricsHistory(nextHistory);
  }

  private updateMetricsHistory(nextHistory: MetricsRecord[]): void {
    const changed =
      nextHistory.length !== this.metricsHistory.length ||
      nextHistory.some((item, index) => JSON.stringify(item) !== JSON.stringify(this.metricsHistory[index]));

    if (!changed) {
      return;
    }

    this.metricsHistory = nextHistory;
    this.postToWebview({
      type: 'metrics',
      history: this.metricsHistory,
      latest: currentMetricsFromHistory(this.metricsHistory),
    });
  }

  private async startTraining(state: TrainFormState): Promise<void> {
    console.log('TrainLens: startTraining called with state:', state);
    if (!this.workspaceRoot) {
      console.log('TrainLens: No workspace root available');
      this.setStatus('idle');
      vscode.window.showWarningMessage('TrainLens needs an open workspace first.');
      return;
    }

    if (this.process) {
      console.log('TrainLens: Training process already running');
      this.setStatus('running');
      vscode.window.showWarningMessage('A training process is already running.');
      return;
    }

    const scriptPath = state.scriptPath.trim();
    const trainDir = state.trainDir.trim();
    const valDir = state.valDir.trim();
    const epochs = parsePositiveInteger(state.epochs.trim());
    const lr = parsePositiveNumber(state.lr.trim());
    const batch = parsePositiveInteger(state.batch.trim());

    if (!scriptPath) {
      this.setStatus('error');
      this.appendLog('error', 'Please choose a training script.');
      vscode.window.showErrorMessage('Please choose a training script.');
      return;
    }
    if (epochs === null) {
      this.setStatus('error');
      this.appendLog('error', 'Epochs must be a positive integer.');
      vscode.window.showErrorMessage('Epochs must be a positive integer.');
      return;
    }
    if (lr === null) {
      this.setStatus('error');
      this.appendLog('error', 'Learning rate must be a positive number.');
      vscode.window.showErrorMessage('Learning rate must be a positive number.');
      return;
    }
    if (batch === null) {
      this.setStatus('error');
      this.appendLog('error', 'Batch size must be a positive integer.');
      vscode.window.showErrorMessage('Batch size must be a positive integer.');
      return;
    }

    const scriptAbs = resolveWorkspacePath(this.workspaceRoot, scriptPath);
    if (!fs.existsSync(scriptAbs)) {
      this.setStatus('error');
      this.appendLog('error', `Training script not found: ${scriptPath}`);
      vscode.window.showErrorMessage(`Training script not found: ${scriptPath}`);
      return;
    }

    const metricsDir = path.dirname(this.metricsFilePath ?? path.join(this.workspaceRoot, METRICS_RELATIVE_PATH));
    fs.mkdirSync(metricsDir, { recursive: true });
    fs.writeFileSync(this.metricsFilePath ?? path.join(this.workspaceRoot, METRICS_RELATIVE_PATH), '', 'utf8');

    this.resetRuntimeView();
    this.setStatus('starting');

    const args = buildSpawnArgs({
      scriptPath,
      trainDir,
      valDir,
      epochs: String(epochs),
      lr: String(lr),
      batch: String(batch),
      device: state.device.trim() || 'auto',
    });

    this.appendLog('system', `Launching: ${buildCommandPreview({
      scriptPath,
      trainDir,
      valDir,
      epochs: String(epochs),
      lr: String(lr),
      batch: String(batch),
      device: state.device.trim() || 'auto',
    })}`);

    this.appendLog('system', `Workspace: ${this.workspaceRoot}`);
    this.appendLog('system', `Metrics: ${METRICS_RELATIVE_PATH}`);

    console.log('TrainLens: Spawning Python process');
    console.log('TrainLens: Command:', 'python', args.join(' '));
    console.log('TrainLens: Working directory:', this.workspaceRoot);

    let settled = false;
    const child = spawn('python', args, {
      cwd: this.workspaceRoot,
      env: {
        ...process.env,
        PYTHONUNBUFFERED: '1',
      },
      windowsHide: true,
      stdio: ['ignore', 'pipe', 'pipe'],
    }) as unknown as ChildProcessWithoutNullStreams;

    this.process = child;
    this.stopRequested = false;
    this.stdoutBuffer = '';
    this.stderrBuffer = '';
    this.setStatus('running');

    child.stdout!.setEncoding('utf8');
    child.stderr!.setEncoding('utf8');

    child.stdout!.on('data', (chunk: string) => {
      this.consumeStreamChunk('stdout', chunk);
    });
    child.stderr!.on('data', (chunk: string) => {
      this.consumeStreamChunk('stderr', chunk);
    });

    const finalize = (kind: 'error' | 'close', code?: number | null, signal?: NodeJS.Signals | null, error?: Error) => {
      if (settled) {
        return;
      }
      settled = true;
      this.process = undefined;
      this.flushStreamBuffers();

      if (this.disposed) {
        this.stopRequested = false;
        return;
      }

      if (kind === 'error') {
        this.stopRequested = false;
        this.setStatus('error');
        const message = error?.message ?? 'Unknown Python launch error.';
        this.appendLog('error', `Failed to start Python: ${message}`);
        vscode.window.showErrorMessage(`Python start failed: ${message}`);
        return;
      }

      if (this.stopRequested) {
        this.appendLog('system', 'Training stopped.');
      } else if (code === 0) {
        this.appendLog('system', 'Training finished.');
      } else {
        const suffix = signal ? ` (signal ${signal})` : '';
        this.appendLog('error', `Training exited with code ${code ?? 'unknown'}${suffix}.`);
      }

      this.stopRequested = false;
      this.setStatus('idle');
    };

    child.once('error', (error: Error) => {
      finalize('error', undefined, undefined, error);
    });

    child.once('close', (code: number | null, signal: NodeJS.Signals | null) => {
      finalize('close', code, signal);
    });
  }

  private async stopTraining(): Promise<void> {
    if (!this.process) {
      return;
    }

    this.stopRequested = true;
    this.setStatus('stopping');
    this.appendLog('system', 'Stopping training...');

    try {
      this.process.kill();
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      this.appendLog('error', `Failed to stop process: ${message}`);
      vscode.window.showWarningMessage(`Failed to stop the training process: ${message}`);
    }
  }

  private terminateProcess(): void {
    if (!this.process) {
      return;
    }

    try {
      this.process.kill();
    } catch {
      // Ignore shutdown errors.
    }

    this.process = undefined;
  }

  private consumeStreamChunk(level: 'stdout' | 'stderr', chunk: string): void {
    if (level === 'stdout') {
      this.stdoutBuffer += chunk;
      this.stdoutBuffer = this.drainBuffer(level, this.stdoutBuffer);
      return;
    }

    this.stderrBuffer += chunk;
    this.stderrBuffer = this.drainBuffer(level, this.stderrBuffer);
  }

  private drainBuffer(level: 'stdout' | 'stderr', buffer: string): string {
    let remainder = buffer;
    let newlineIndex = remainder.indexOf('\n');
    while (newlineIndex >= 0) {
      const rawLine = remainder.slice(0, newlineIndex).replace(/\r$/, '');
      remainder = remainder.slice(newlineIndex + 1);
      if (rawLine.length > 0) {
        this.appendLog(level, rawLine);
      }
      newlineIndex = remainder.indexOf('\n');
    }
    return remainder;
  }

  private flushStreamBuffers(): void {
    if (this.stdoutBuffer.trim().length > 0) {
      this.appendLog('stdout', this.stdoutBuffer.trimEnd());
    }
    if (this.stderrBuffer.trim().length > 0) {
      this.appendLog('stderr', this.stderrBuffer.trimEnd());
    }
    this.stdoutBuffer = '';
    this.stderrBuffer = '';
  }

  private resetRuntimeView(): void {
    this.logs = [];
    this.metricsHistory = [];
    this.postToWebview({ type: 'reset' });
  }

  private setStatus(status: RuntimeStatus): void {
    this.status = status;
    this.postToWebview({ type: 'status', status });
  }

  private appendLog(level: LogEntry['level'], text: string): void {
    const lines = text.split(/\r?\n/).filter((line) => line.length > 0);
    if (lines.length === 0) {
      return;
    }

    for (const line of lines) {
      this.logs.push({ level, text: line });
    }

    if (this.logs.length > MAX_LOG_LINES) {
      this.logs = this.logs.slice(this.logs.length - MAX_LOG_LINES);
    }

    for (const line of lines) {
      this.postToWebview({
        type: 'log',
        entry: {
          level,
          text: line,
        },
      });
    }
  }

  private sendSnapshot(): void {
    this.postToWebview({
      type: 'snapshot',
      formState: this.currentFormState,
      status: this.status,
      logs: this.logs,
      metricsHistory: this.metricsHistory,
      latest: currentMetricsFromHistory(this.metricsHistory),
    });
  }

  private postToWebview(message: unknown): void {
    if (!this.panel) {
      return;
    }
    void this.panel.webview.postMessage(message);
  }

  private renderHtml(webview: vscode.Webview): string {
    const nonce = getNonce();
    const bootstrapState = safeJson(this.currentFormState);

    return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src ${webview.cspSource} data:; style-src ${webview.cspSource} 'unsafe-inline'; script-src 'nonce-${nonce}';">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>TrainLens</title>
  <style>
    :root {
      color-scheme: dark;
      --bg: #0d1117;
      --panel: #161b22;
      --panel-2: #0f141a;
      --border: #283041;
      --text: #d7dee8;
      --muted: #8b97a8;
      --accent: #4cc9f0;
      --accent-2: #22c55e;
      --warn: #f59e0b;
      --danger: #ef4444;
      --chip: #1f2937;
      --shadow: rgba(0, 0, 0, 0.24);
    }

    * {
      box-sizing: border-box;
    }

    html, body {
      margin: 0;
      padding: 0;
      width: 100%;
      height: 100%;
      background: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      font-size: 13px;
    }

    body {
      overflow: auto;
    }

    .app {
      min-height: 100vh;
      padding: 12px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    .topbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding-bottom: 8px;
      border-bottom: 1px solid var(--border);
    }

    .brand {
      display: flex;
      align-items: baseline;
      gap: 8px;
    }

    .eyebrow {
      color: var(--muted);
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }

    h1 {
      margin: 0;
      font-size: 16px;
      font-weight: 600;
      line-height: 1;
    }

    .topbar-actions {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
    }

    .status-pill {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      height: 26px;
      padding: 0 10px;
      border-radius: 999px;
      border: 1px solid var(--border);
      background: var(--chip);
      color: var(--text);
      font-size: 11px;
      font-weight: 600;
    }

    .status-pill::before {
      content: '';
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: var(--muted);
      flex: 0 0 auto;
    }

    .status-idle::before { background: var(--muted); }
    .status-starting::before { background: var(--warn); }
    .status-running::before { background: var(--accent-2); }
    .status-stopping::before { background: var(--warn); }
    .status-error::before { background: var(--danger); }

    button {
      appearance: none;
      border: 1px solid var(--border);
      border-radius: 4px;
      height: 28px;
      padding: 0 12px;
      color: var(--text);
      background: #1b2430;
      font: inherit;
      font-size: 12px;
      cursor: pointer;
      transition: background 120ms ease, border-color 120ms ease;
    }

    button:hover:not(:disabled) {
      background: #223041;
      border-color: #3a4b62;
    }

    button:active:not(:disabled) {
      transform: translateY(1px);
    }

    button:disabled {
      cursor: not-allowed;
      opacity: 0.45;
    }

    .primary {
      background: rgba(76, 201, 240, 0.16);
      border-color: rgba(76, 201, 240, 0.35);
    }

    .danger {
      background: rgba(239, 68, 68, 0.13);
      border-color: rgba(239, 68, 68, 0.35);
    }

    .grid {
      display: grid;
      gap: 12px;
    }

    .main-layout {
      display: grid;
      grid-template-columns: 340px 1fr;
      gap: 12px;
      align-items: start;
    }

    .panel {
      border: 1px solid var(--border);
      border-radius: 6px;
      background: var(--panel);
      padding: 12px;
    }

    .panel-title {
      margin: 0 0 10px;
      font-size: 11px;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.5px;
      font-weight: 600;
    }

    .form-grid {
      display: grid;
      gap: 10px;
    }

    .field {
      display: grid;
      gap: 4px;
    }

    .field label {
      font-size: 11px;
      color: var(--muted);
    }

    .field input,
    .field select {
      width: 100%;
      height: 30px;
      border-radius: 4px;
      border: 1px solid var(--border);
      background: var(--panel-2);
      color: var(--text);
      padding: 0 8px;
      font: inherit;
      font-size: 12px;
      outline: none;
    }

    .field input:focus,
    .field select:focus {
      border-color: rgba(76, 201, 240, 0.55);
      box-shadow: 0 0 0 1px rgba(76, 201, 240, 0.2);
    }

    .preview {
      margin: 8px 0 0;
      padding: 8px;
      border-radius: 4px;
      border: 1px solid var(--border);
      background: var(--panel-2);
      color: #d7dee8;
      overflow: auto;
      white-space: pre-wrap;
      word-break: break-word;
      line-height: 1.4;
      font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
      font-size: 11px;
      max-height: 80px;
    }

    .runtime-panel {
      display: grid;
      gap: 12px;
    }

    .metrics-row {
      display: grid;
      grid-template-columns: 200px 1fr;
      gap: 12px;
      align-items: start;
    }

    .progress-card {
      border: 1px solid var(--border);
      border-radius: 6px;
      background: var(--panel-2);
      padding: 12px;
      display: grid;
      place-items: center;
    }

    .progress-ring {
      width: 180px;
      height: 180px;
      display: block;
    }

    .progress-center {
      font-weight: 700;
      font-size: 16px;
      fill: var(--text);
    }

    .progress-sub {
      font-size: 10px;
      fill: var(--muted);
    }

    .stats-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 10px;
    }

    .stat {
      border: 1px solid var(--border);
      border-radius: 6px;
      background: var(--panel-2);
      padding: 10px;
      display: grid;
      gap: 6px;
    }

    .stat-title {
      font-size: 10px;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }

    .stat-value {
      font-size: 18px;
      line-height: 1;
      font-weight: 700;
      word-break: break-word;
    }

    .chart-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 12px;
    }

    .chart-panel {
      border: 1px solid var(--border);
      border-radius: 6px;
      background: var(--panel-2);
      padding: 10px;
      display: grid;
      gap: 8px;
    }

    .chart-header {
      display: flex;
      align-items: baseline;
      justify-content: space-between;
      gap: 8px;
    }

    .chart-title {
      font-size: 11px;
      color: var(--text);
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }

    .chart-caption {
      font-size: 10px;
      color: var(--muted);
    }

    canvas {
      width: 100%;
      height: 200px;
      display: block;
      border-radius: 4px;
      background: #0c1015;
      border: 1px solid #222b38;
    }

    .log-output {
      height: 180px;
      overflow: auto;
      border: 1px solid var(--border);
      border-radius: 4px;
      background: #0b0f14;
      padding: 8px;
      font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
      font-size: 11px;
      line-height: 1.4;
    }

    .log-line {
      white-space: pre-wrap;
      word-break: break-word;
      margin: 0 0 1px;
    }

    .log-system { color: #9fb7d1; }
    .log-stdout { color: #cbd5e1; }
    .log-stderr { color: #f59e0b; }
    .log-error { color: #f87171; }

    @media (max-width: 1200px) {
      .main-layout {
        grid-template-columns: 1fr;
      }

      .metrics-row {
        grid-template-columns: 1fr;
      }

      .chart-grid {
        grid-template-columns: 1fr;
      }
    }
  </style>
</head>
<body>
  <div class="app">
    <header class="topbar">
      <div class="brand">
        <div class="eyebrow">TrainLens</div>
        <h1>Training Dashboard</h1>
      </div>
      <div class="topbar-actions">
        <span id="statusPill" class="status-pill status-idle">Idle</span>
        <button id="startBtn" class="primary">Start Training</button>
        <button id="stopBtn" class="danger" disabled>Stop Training</button>
      </div>
    </header>

    <main class="main-layout">
      <aside class="panel">
        <div class="panel-title">Training Config</div>
        <div class="form-grid">
          <div class="field">
            <label for="scriptPath">Training script</label>
            <input id="scriptPath" type="text" value="scripts/mock_train.py">
          </div>
          <div class="field">
            <label for="trainDir">Train set</label>
            <input id="trainDir" type="text" value="./dataset/train">
          </div>
          <div class="field">
            <label for="valDir">Val set</label>
            <input id="valDir" type="text" value="./dataset/val">
          </div>
          <div class="field">
            <label for="epochs">Epochs</label>
            <input id="epochs" type="number" min="1" step="1" value="20">
          </div>
          <div class="field">
            <label for="lr">Learning rate</label>
            <input id="lr" type="number" min="0" step="any" value="0.001">
          </div>
          <div class="field">
            <label for="batch">Batch size</label>
            <input id="batch" type="number" min="1" step="1" value="16">
          </div>
          <div class="field">
            <label for="device">Device</label>
            <select id="device">
              <option value="auto">auto</option>
              <option value="cpu">cpu</option>
              <option value="cuda:0">cuda:0</option>
              <option value="cuda:1">cuda:1</option>
            </select>
          </div>
        </div>
        <div class="panel-title" style="margin-top: 12px;">Command Preview</div>
        <pre class="preview" id="commandPreview"></pre>
      </aside>

      <div class="runtime-panel">
        <div class="metrics-row">
          <div class="progress-card">
            <svg class="progress-ring" viewBox="0 0 120 120" aria-label="Training progress">
              <circle cx="60" cy="60" r="46" fill="none" stroke="#243042" stroke-width="10"></circle>
              <circle id="progressStroke" cx="60" cy="60" r="46" fill="none" stroke="#4cc9f0" stroke-linecap="round" stroke-width="10" stroke-dasharray="289" stroke-dashoffset="289" transform="rotate(-90 60 60)"></circle>
              <text x="60" y="56" text-anchor="middle" class="progress-center" id="progressPercent">0%</text>
              <text x="60" y="74" text-anchor="middle" class="progress-sub" id="progressEpoch">-- / --</text>
            </svg>
          </div>
          <div class="stats-grid">
            <div class="stat">
              <div class="stat-title">Current acc</div>
              <div class="stat-value" id="currentAcc">-</div>
            </div>
            <div class="stat">
              <div class="stat-title">Best acc</div>
              <div class="stat-value" id="bestAcc">-</div>
            </div>
            <div class="stat">
              <div class="stat-title">Current loss</div>
              <div class="stat-value" id="currentLoss">-</div>
            </div>
            <div class="stat">
              <div class="stat-title">Best loss</div>
              <div class="stat-value" id="bestLoss">-</div>
            </div>
          </div>
        </div>

        <div class="chart-grid">
          <div class="chart-panel">
            <div class="chart-header">
              <div class="chart-title">Accuracy</div>
              <div class="chart-caption" id="accCaption">No data</div>
            </div>
            <canvas id="accChart"></canvas>
          </div>
          <div class="chart-panel">
            <div class="chart-header">
              <div class="chart-title">Loss</div>
              <div class="chart-caption" id="lossCaption">No data</div>
            </div>
            <canvas id="lossChart"></canvas>
          </div>
        </div>

        <div class="panel">
          <div class="panel-title">Training Logs</div>
          <div id="logOutput" class="log-output"></div>
        </div>
      </div>
    </main>
  </div>

  <script nonce="${nonce}">
    const vscode = acquireVsCodeApi();
    const bootstrapState = ${bootstrapState};
    const savedState = vscode.getState();
    const initialState = savedState && savedState.formState ? savedState.formState : bootstrapState;

    const els = {
      statusPill: document.getElementById('statusPill'),
      startBtn: document.getElementById('startBtn'),
      stopBtn: document.getElementById('stopBtn'),
      scriptPath: document.getElementById('scriptPath'),
      trainDir: document.getElementById('trainDir'),
      valDir: document.getElementById('valDir'),
      epochs: document.getElementById('epochs'),
      lr: document.getElementById('lr'),
      batch: document.getElementById('batch'),
      device: document.getElementById('device'),
      commandPreview: document.getElementById('commandPreview'),
      progressStroke: document.getElementById('progressStroke'),
      progressPercent: document.getElementById('progressPercent'),
      progressEpoch: document.getElementById('progressEpoch'),
      currentAcc: document.getElementById('currentAcc'),
      bestAcc: document.getElementById('bestAcc'),
      currentLoss: document.getElementById('currentLoss'),
      bestLoss: document.getElementById('bestLoss'),
      accChart: document.getElementById('accChart'),
      lossChart: document.getElementById('lossChart'),
      accCaption: document.getElementById('accCaption'),
      lossCaption: document.getElementById('lossCaption'),
      logOutput: document.getElementById('logOutput'),
    };

    const state = {
      runtimeStatus: 'idle',
      logs: [],
      metricsHistory: [],
      latestMetrics: null,
    };

    const progressRadius = 46;
    const progressCircumference = 2 * Math.PI * progressRadius;

    function clamp(value, min, max) {
      return Math.min(max, Math.max(min, value));
    }

    function formatNumber(value, digits) {
      return typeof value === 'number' && Number.isFinite(value) ? value.toFixed(digits) : '-';
    }

    function formatEpochValue(value) {
      return typeof value === 'number' && Number.isFinite(value) ? String(Math.round(value)) : '--';
    }

    function buildCommandPreview(formState) {
      function q(value) {
        return /[\s"'\\]/.test(value) || value.indexOf(String.fromCharCode(96)) >= 0 ? '"' + value.replace(/\\/g, '\\\\').replace(/"/g, '\\"') + '"' : value;
      }
      return [
        'python',
        formState.scriptPath.trim(),
        '--train',
        formState.trainDir.trim(),
        '--val',
        formState.valDir.trim(),
        '--epochs',
        formState.epochs.trim(),
        '--lr',
        formState.lr.trim(),
        '--batch',
        formState.batch.trim(),
        '--device',
        formState.device.trim(),
        '--log',
        'runs/current/metrics.jsonl',
      ].map(q).join(' ');
    }

    function readFormState() {
      return {
        scriptPath: els.scriptPath.value,
        trainDir: els.trainDir.value,
        valDir: els.valDir.value,
        epochs: els.epochs.value,
        lr: els.lr.value,
        batch: els.batch.value,
        device: els.device.value,
      };
    }

    function applyFormState(formState, quiet) {
      els.scriptPath.value = formState.scriptPath || '';
      els.trainDir.value = formState.trainDir || '';
      els.valDir.value = formState.valDir || '';
      els.epochs.value = formState.epochs || '';
      els.lr.value = formState.lr || '';
      els.batch.value = formState.batch || '';
      els.device.value = formState.device || 'auto';
      updateCommandPreview();
      if (!quiet) {
        persistFormState();
      }
    }

    function persistFormState() {
      const formState = readFormState();
      vscode.setState({ formState: formState });
      vscode.postMessage({ type: 'stateChanged', state: formState });
    }

    function updateCommandPreview() {
      els.commandPreview.textContent = buildCommandPreview(readFormState());
    }

    function setStatus(status) {
      state.runtimeStatus = status;
      const label = status === 'idle' ? 'Idle'
        : status === 'starting' ? 'Starting'
        : status === 'running' ? 'Running'
        : status === 'stopping' ? 'Stopping'
        : 'Error';
      els.statusPill.textContent = label;
      els.statusPill.className = 'status-pill status-' + status;
      const runningLike = status === 'starting' || status === 'running' || status === 'stopping';
      els.startBtn.disabled = runningLike;
      els.stopBtn.disabled = !runningLike;
    }

    function updateProgress(latest) {
      const epoch = latest && typeof latest.epoch === 'number' ? latest.epoch : null;
      const totalEpoch = latest && typeof latest.total_epoch === 'number' ? latest.total_epoch : null;
      let ratio = 0;
      if (latest && typeof latest.progress === 'number') {
        const prog = latest.progress;
        ratio = prog <= 1 ? prog : prog / 100;
      } else if (epoch && totalEpoch) {
        ratio = epoch / totalEpoch;
      }
      ratio = clamp(ratio, 0, 1);
      const offset = progressCircumference * (1 - ratio);
      els.progressStroke.setAttribute('stroke-dasharray', String(progressCircumference));
      els.progressStroke.setAttribute('stroke-dashoffset', String(offset));
      els.progressPercent.textContent = Math.round(ratio * 100) + '%';
      els.progressEpoch.textContent = (epoch ? formatEpochValue(epoch) : '--') + ' / ' + (totalEpoch ? formatEpochValue(totalEpoch) : '--');
    }

    function updateMetricCards(latest) {
      els.currentAcc.textContent = formatNumber(latest && latest.acc, 4);
      els.bestAcc.textContent = formatNumber(latest && latest.best_acc, 4);
      const currentLoss = latest ? (typeof latest.val_loss === 'number' ? latest.val_loss : typeof latest.train_loss === 'number' ? latest.train_loss : latest.loss) : null;
      els.currentLoss.textContent = formatNumber(currentLoss, 4);
      els.bestLoss.textContent = formatNumber(latest && latest.best_loss, 4);
      els.accCaption.textContent = latest && typeof latest.acc === 'number' ? 'Last acc: ' + formatNumber(latest.acc, 4) : 'No data';
      const lossCaptionValue = latest ? (typeof latest.val_loss === 'number' ? latest.val_loss : typeof latest.train_loss === 'number' ? latest.train_loss : latest.loss) : null;
      els.lossCaption.textContent = typeof lossCaptionValue === 'number' ? 'Last loss: ' + formatNumber(lossCaptionValue, 4) : 'No data';
    }

    function trimChartPoints(history) {
      return history.slice(Math.max(0, history.length - ${MAX_CHART_POINTS}));
    }

    function drawChart(canvas, points, options) {
      const rect = canvas.getBoundingClientRect();
      const dpr = window.devicePixelRatio || 1;
      if (!rect.width || !rect.height) {
        return;
      }
      canvas.width = Math.round(rect.width * dpr);
      canvas.height = Math.round(rect.height * dpr);
      const ctx = canvas.getContext('2d');
      if (!ctx) {
        return;
      }
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, rect.width, rect.height);
      ctx.fillStyle = '#0c1015';
      ctx.fillRect(0, 0, rect.width, rect.height);

      const padding = { left: 48, right: 18, top: 16, bottom: 28 };
      const width = rect.width - padding.left - padding.right;
      const height = rect.height - padding.top - padding.bottom;

      ctx.strokeStyle = '#213042';
      ctx.lineWidth = 1;
      ctx.font = '11px ui-monospace, SFMono-Regular, Consolas, monospace';
      ctx.fillStyle = '#7f8da0';

      for (let i = 0; i <= 4; i += 1) {
        const y = padding.top + (height / 4) * i;
        ctx.beginPath();
        ctx.moveTo(padding.left, y);
        ctx.lineTo(rect.width - padding.right, y);
        ctx.stroke();
      }

      if (!points.length) {
        ctx.fillStyle = '#7f8da0';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText('No data yet', rect.width / 2, rect.height / 2);
        return;
      }

      const ys = points.map(function (item) { return item.y; });
      let minY = Math.min.apply(null, ys);
      let maxY = Math.max.apply(null, ys);
      if (minY === maxY) {
        const delta = minY === 0 ? 1 : Math.abs(minY) * 0.1;
        minY -= delta;
        maxY += delta;
      } else {
        const paddingY = (maxY - minY) * 0.12;
        minY -= paddingY;
        maxY += paddingY;
      }

      function mapX(index) {
        if (points.length === 1) {
          return padding.left + width / 2;
        }
        return padding.left + (width * index) / (points.length - 1);
      }

      function mapY(value) {
        const ratio = (value - minY) / (maxY - minY);
        return padding.top + height - ratio * height;
      }

      ctx.fillStyle = '#6c7a90';
      ctx.textAlign = 'right';
      ctx.textBaseline = 'middle';
      ctx.fillText(maxY.toFixed(3), padding.left - 8, padding.top + 4);
      ctx.fillText(minY.toFixed(3), padding.left - 8, padding.top + height - 4);

      ctx.strokeStyle = options.gridColor;
      ctx.fillStyle = options.lineColor;
      ctx.lineWidth = 2;

      ctx.beginPath();
      points.forEach(function (point, index) {
        const x = mapX(index);
        const y = mapY(point.y);
        if (index === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      });
      ctx.stroke();

      ctx.fillStyle = options.fillColor;
      ctx.beginPath();
      points.forEach(function (point, index) {
        const x = mapX(index);
        const y = mapY(point.y);
        if (index === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      });
      ctx.lineTo(mapX(points.length - 1), padding.top + height);
      ctx.lineTo(mapX(0), padding.top + height);
      ctx.closePath();
      ctx.fill();

      const lastPoint = points[points.length - 1];
      const lastX = mapX(points.length - 1);
      const lastY = mapY(lastPoint.y);
      ctx.fillStyle = options.lineColor;
      ctx.beginPath();
      ctx.arc(lastX, lastY, 4, 0, Math.PI * 2);
      ctx.fill();
    }

    function renderCharts() {
      const history = trimChartPoints(state.metricsHistory);
      const accPoints = history
        .map(function (item, index) {
          const y = typeof item.acc === 'number' ? item.acc : null;
          const x = typeof item.epoch === 'number' ? item.epoch : index + 1;
          return y === null ? null : { x: x, y: y };
        })
        .filter(Boolean);
      const lossPoints = history
        .map(function (item, index) {
          const loss = typeof item.val_loss === 'number' ? item.val_loss : typeof item.train_loss === 'number' ? item.train_loss : (typeof item.loss === 'number' ? item.loss : null);
          const x = typeof item.epoch === 'number' ? item.epoch : index + 1;
          return loss === null ? null : { x: x, y: loss };
        })
        .filter(Boolean);

      drawChart(els.accChart, accPoints, {
        lineColor: '#4cc9f0',
        fillColor: 'rgba(76, 201, 240, 0.12)',
        gridColor: '#203040',
      });
      drawChart(els.lossChart, lossPoints, {
        lineColor: '#f59e0b',
        fillColor: 'rgba(245, 158, 11, 0.13)',
        gridColor: '#2b2a1f',
      });
    }

    function renderLogs() {
      els.logOutput.textContent = '';
      state.logs.forEach(function (entry) {
        const line = document.createElement('div');
        line.className = 'log-line log-' + entry.level;
        line.textContent = entry.text;
        els.logOutput.appendChild(line);
      });
      els.logOutput.scrollTop = els.logOutput.scrollHeight;
    }

    function renderRuntime() {
      updateProgress(state.latestMetrics);
      updateMetricCards(state.latestMetrics);
      renderCharts();
      renderLogs();
    }

    function clearRuntimeData() {
      state.logs = [];
      state.metricsHistory = [];
      state.latestMetrics = null;
      renderRuntime();
    }

    function pushLog(entry) {
      state.logs.push(entry);
      if (state.logs.length > ${MAX_LOG_LINES}) {
        state.logs = state.logs.slice(state.logs.length - ${MAX_LOG_LINES});
      }
      renderLogs();
    }

    function applySnapshot(snapshot) {
      if (snapshot.formState) {
        applyFormState(snapshot.formState, true);
      }
      state.runtimeStatus = snapshot.status || 'idle';
      state.logs = Array.isArray(snapshot.logs) ? snapshot.logs.slice() : [];
      state.metricsHistory = Array.isArray(snapshot.metricsHistory) ? snapshot.metricsHistory.slice() : [];
      state.latestMetrics = snapshot.latest || (state.metricsHistory.length ? state.metricsHistory[state.metricsHistory.length - 1] : null);
      setStatus(state.runtimeStatus);
      renderRuntime();
    }

    els.startBtn.addEventListener('click', function () {
      console.log('Start button clicked!');
      alert('Start button clicked! Sending message to extension...');
      setStatus('starting');
      const formState = readFormState();
      console.log('Form state:', formState);
      vscode.postMessage({ type: 'start', state: formState });
      console.log('Message sent');
    });

    els.stopBtn.addEventListener('click', function () {
      setStatus('stopping');
      vscode.postMessage({ type: 'stop' });
    });

    [els.scriptPath, els.trainDir, els.valDir, els.epochs, els.lr, els.batch, els.device].forEach(function (element) {
      element.addEventListener('input', function () {
        updateCommandPreview();
        persistFormState();
      });
      element.addEventListener('change', function () {
        updateCommandPreview();
        persistFormState();
      });
    });

    window.addEventListener('resize', function () {
      renderCharts();
    });

    window.addEventListener('message', function (event) {
      const message = event.data;
      if (!message || !message.type) {
        return;
      }
      if (message.type === 'snapshot') {
        applySnapshot(message);
        return;
      }
      if (message.type === 'status') {
        setStatus(message.status);
        return;
      }
      if (message.type === 'reset') {
        clearRuntimeData();
        return;
      }
      if (message.type === 'log') {
        pushLog(message.entry);
        return;
      }
      if (message.type === 'metrics') {
        state.metricsHistory = Array.isArray(message.history) ? message.history.slice() : [];
        state.latestMetrics = message.latest || (state.metricsHistory.length ? state.metricsHistory[state.metricsHistory.length - 1] : null);
        updateProgress(state.latestMetrics);
        updateMetricCards(state.latestMetrics);
        renderCharts();
      }
    });

    applyFormState(initialState || ${safeJson(DEFAULT_FORM_STATE)}, true);
    setStatus('idle');
    updateCommandPreview();
    renderRuntime();
    vscode.setState({ formState: readFormState() });
    vscode.postMessage({ type: 'ready' });
  </script>
</body>
</html>`;
  }
}

let controller: TrainLensController | undefined;

export function activate(context: vscode.ExtensionContext): void {
  const fs = require('fs');
  const path = require('path');
  const testFile = path.join(__dirname, '..', '..', 'ACTIVATION_TEST.txt');
  try {
    if (fs.existsSync(testFile)) {
      fs.unlinkSync(testFile);
      fs.writeFileSync(testFile.replace('.txt', '_DELETED.txt'), 'Extension activated at ' + new Date().toISOString());
    }
  } catch (e) {}

  console.log('TrainLens extension activated');
  vscode.window.showInformationMessage('TrainLens extension activated!');
  controller = new TrainLensController();
  context.subscriptions.push(controller);
  context.subscriptions.push(
    vscode.commands.registerCommand('trainlens.openDashboard', async () => {
      console.log('TrainLens dashboard command triggered');
      await controller?.openDashboard();
    }),
  );
  console.log('TrainLens command registered: trainlens.openDashboard');
}

export function deactivate(): void {
  controller?.dispose();
  controller = undefined;
}
