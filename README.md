# Agent Model Manager

本地桌面应用，用来统一管理 `opencode` 和 `oh-my-openagent` 的模型配置。

## 技术栈

- `FastAPI`：读取、校验、preview、apply 配置
- `Vue 3 + Pinia + Element Plus`：配置管理界面
- `Electron`：桌面壳
- `PyInstaller`：把 Python backend 打成内置可执行文件

## 本地开发

### 1. 安装依赖

```powershell
python -m pip install -r backend\requirements.txt
npm install
```

### 2. 启动开发版桌面应用

```powershell
npm run dev
```

- 前端：`http://localhost:5173`
- 后端：`http://127.0.0.1:8765`
- Electron 会自动拉起桌面窗口

### 3. 运行测试

```powershell
npm run backend:test
npm run test:frontend
npm run test:electron
```

### 4. 打包 Windows 文件夹版

```powershell
npm run dist
```

这会先构建前端，再用 `PyInstaller` 打后端，最后用 `electron-builder` 输出文件夹版桌面应用。

### 5. 一键打包

如果你不想手动输命令，直接在项目根目录运行：

```powershell
.\build-portable.cmd
```

这个脚本会先检查打包依赖：

- 如果缺少 `node_modules` 里的 `electron-builder`，会先执行 `npm install`
- 如果当前 Python 环境里没有 `PyInstaller`，会先执行 `python -m pip install -r backend\requirements.txt`
- 会先关闭已经打开的 `Agent Model Manager` 和内置 backend 进程，避免打包文件被占用
- 会先清掉 `dist\win-unpacked` 和旧的 Electron 中间产物，减少“看起来卡住”的情况

依赖就绪后，它会按下面的顺序自动执行：

```powershell
npm run test:frontend
npm run test:electron
npm run backend:test
npm run build:frontend
npm run build:backend
npm run build:desktop
```

打包完成后，文件夹版输出在：

```text
dist\win-unpacked\Agent Model Manager.exe
```

发布或移动时需要带上整个 `dist\win-unpacked` 文件夹，不能只拿里面的 `exe`。

完整日志会写到：

```text
build-portable.log
```

如果你是第一次在这台机器上打包，建议先确认下面两项：

- `python --version`
- `node --version`

如果你看到窗口在最后一步停很久，优先看 `build-portable.log` 里最后几行；Electron 的文件夹打包阶段本身可能需要 1 到 2 分钟。

## 环境要求

- Python 3.9+
- Node.js 22+
- 不再需要 Rust / Cargo
