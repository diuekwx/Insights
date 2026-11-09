const { app, BrowserWindow } = require('electron');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');

// use the project's venv when it exists (that's where requirements.txt is
// installed); otherwise fall back to whatever python is on PATH
const venvPython = path.join(__dirname, 'venv', 'Scripts', 'python.exe');
const pythonExe = fs.existsSync(venvPython) ? venvPython : 'python';

let python;

function createWindow() {
  // (no preload: preload.js does not exist)
  const win = new BrowserWindow({
    width: 1000,
    height: 700,
  });

  win.loadFile('public/index.html');
}

function startBackend() {
  // cwd: resolve backend/server.py from the app folder, not wherever electron was launched
  python = spawn(pythonExe, ['backend/server.py'], { cwd: __dirname });
  python.stdout.on('data', (data) => console.log(`Python: ${data}`));
  python.stderr.on('data', (data) => console.error(`Python error: ${data}`));
}

app.whenReady().then(() => {
  // start the server once; createWindow can run again on 'activate'
  startBackend();
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

// child processes outlive Electron on Windows; without this the server keeps
// port 5000 (and any recording loop) alive after the window is closed
app.on('will-quit', () => {
  if (python) python.kill();
});
