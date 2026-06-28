曾经在站上，有一个get_jobs，我找工作的时候用了，发现，几乎用不了，不同的人部署到本地会出现不同的bug，所以，我打算自己做一个类似的，甚至是超越的，我做了，make_jobs_ai出现了，但是还没有做完，我就找到工作了，所以，这个不算是完成品，完成了80%左右吧，站上的各位大神可以互勉，想找工作的朋友们可以先用着，后面靠你们来完善它了，加油，会找到最钟意的工作的！！！后面的完善工作就交给站上的各位大神了！！！抱拳，抱拳！！！交流：QQ1574098726

# make-jobs-ai

智能求职助手 - 一站式求职自动化平台

## 功能特性

- **多平台岗位爬取** - 支持 BOSS直聘、智联招聘、猎聘、前程无忧、应届生求职
- **AI 简历生成** - 美化后简历 & 市场专业需求简历
- **智能匹配分析** - 本地规则匹配 / AI 匹配（支持 13+ API 提供商）
- **投递管理** - 岗位导入、匹配分析、投递记录

## 环境要求

- **Python** >= 3.8
- **Node.js** >= 16
- **Git**

### Windows 用户额外要求

- 安装 [Playwright 浏览器驱动](https://playwright.dev/python/docs/browsers):
  ```bash
  pip install playwright
  playwright install chromium
  ```

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/jc1574098726-star/make-jobs-ai.git
cd make-jobs-ai
```

### 2. 安装后端依赖

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

pip install -e .
```

### 3. 安装 Playwright 浏览器

```bash
playwright install chromium
```

### 4. 配置环境变量（可选）

复制 `.env.example` 为 `.env` 并填写配置：

```bash
cp .env.example .env
```

关键配置项：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `APP_HOST` | 监听地址 | `127.0.0.1` |
| `APP_PORT` | 监听端口 | `8000` |
| `FRONTEND_ORIGIN` | 前端地址（CORS） | `http://127.0.0.1:5173` |
| `ANTHROPIC_API_KEY` | Anthropic API 密钥（可选） | 空 |
| `CLAUDE_MODEL` | 默认 AI 模型 | `claude-opus-4-7` |

> **提示**：API 密钥也可以在前端「API 设置」中配置，支持 13+ 提供商。

### 5. 安装前端依赖

```bash
cd ../frontend
npm install
```

### 6. 启动服务

```bash
# 终端1：启动后端
cd backend
uvicorn app.main:app --reload

# 终端2：启动前端
cd frontend
npm run dev
```

### 7. 访问应用

打开浏览器访问 http://127.0.0.1:5173

## 支持的 API 提供商

在前端「API 设置」中选择并配置：

| 提供商 | 说明 |
|--------|------|
| Anthropic (Claude) | Claude 系列模型 |
| OpenAI (ChatGPT) | GPT-4o 等 |
| DeepSeek | DeepSeek-V3/R1 |
| 小米 MiMo | MiMo 系列 |
| 硅基流动 (SiliconFlow) | 开源模型托管 |
| 火山引擎 (ByteDance) | 豆包系列 |
| NVIDIA | Llama/Nemotron |
| 智谱 (GLM) | GLM-4 系列 |
| MiniMax | abab 系列 |
| Kimi (Moonshot) | Moonshot 系列 |
| StepFun (阶跃星辰) | Step 系列 |
| 千问 (阿里云) | Qwen 系列 |
| Google Gemini | Gemini 系列 |
| 自定义 | 任何 OpenAI 兼容接口 |

## 常见问题

### Q: 后端启动报错 `ModuleNotFoundError`

A: 确保已激活虚拟环境并安装依赖：
```bash
cd backend
venv\Scripts\activate  # Windows
pip install -e .
```

### Q: Playwright 报错 `BrowserType.launch`

A: 需要安装浏览器驱动：
```bash
playwright install chromium
```

### Q: 前端显示 "Failed to fetch"

A: 确保后端已启动且端口正确（默认 8000）。

### Q: 岗位爬取失败

A: 部分平台可能需要登录或有反爬机制，建议使用手动导入 JD 的方式。

## 技术栈

- **后端**: FastAPI + SQLModel + SQLite + Playwright
- **前端**: React + Vite
- **AI**: 支持多种 OpenAI 兼容 API

## License

MIT
