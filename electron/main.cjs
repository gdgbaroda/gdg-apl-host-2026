const { app, BrowserWindow, globalShortcut } = require('electron');
const path = require('path');
const { pathToFileURL } = require('url');

const CHROME_UA =
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36';

function quizUrl() {
  if (!app.isPackaged && process.env.NODE_ENV !== 'production') {
    return 'http://localhost:5173/';
  }
  // In production, Vite builds to ./dist next to package.json (inside app.asar).
  return pathToFileURL(path.join(__dirname, '..', 'dist', 'index.html')).toString();
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1600,
    height: 900,
    backgroundColor: '#000000',
    webPreferences: {
      webviewTag: true,
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  win.loadFile(path.join(__dirname, '..', 'shell.html'));

  win.webContents.once('did-finish-load', () => {
    const url = quizUrl();
    win.webContents.executeJavaScript(
      `document.getElementById('quiz').src = ${JSON.stringify(url)};`,
    );
  });

  win.webContents.on('did-attach-webview', (_e, webContents) => {
    webContents.setUserAgent(CHROME_UA);
  });

  globalShortcut.register('F11', () => {
    win.setFullScreen(!win.isFullScreen());
  });
}

app.whenReady().then(createWindow);
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});
