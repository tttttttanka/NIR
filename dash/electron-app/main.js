const { app, BrowserWindow } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;
let pythonProcess;

function createWindow() {
  // Создаем окно
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true
    }
  });

  // Пути к файлам
  const projectRoot = path.join(__dirname, '..');
  const appPyPath = path.join(projectRoot, 'app.py');

  // Запускаем Python приложение
  pythonProcess = spawn('python', [appPyPath], {
    cwd: projectRoot
  });

  // Логируем вывод Python
  pythonProcess.stdout.on('data', (data) => {
    console.log(data.toString());
  });

  pythonProcess.stderr.on('data', (data) => {
    console.error(data.toString());
  });

  // Ждем 3 секунды и загружаем приложение
  setTimeout(() => {
    mainWindow.loadURL('http://localhost:8050');
  }, 3000);
}

// Запуск приложения
app.whenReady().then(createWindow);

// Закрытие приложения
app.on('window-all-closed', () => {
  if (pythonProcess) pythonProcess.kill();
  app.quit();
});