曾经在站上，有一个get_jobs，我找工作的时候用了，发现，几乎用不了，不同的人部署到本地会出现不同的bug，所以，我打算自己做一个类似的，甚至是超越的，我做了，make_jobs_ai出现了，但是还没有做完，我就找到工作了，所以，这个不算是完成品，完成了80%左右吧，站上的各位大神可以互勉，想找工作的朋友们可以先用着，后面靠你们来完善它了，加油，会找到最钟意的工作的！！！

# make-jobs-ai

智能求职助手 - 一站式求职自动化平台

## 功能特性

- **多平台岗位爬取** - 支持 BOSS直聘、智联招聘、猎聘、前程无忧、应届生求职
- **AI 简历生成** - 美化后简历 & 市场专业需求简历
- **智能匹配分析** - 本地规则匹配 / AI 匹配（支持 13+ API 提供商）
- **投递管理** - 岗位导入、匹配分析、投递记录

## 快速开始

### 安装依赖

```bash
# 后端
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e .

# 前端
cd frontend
npm install
```

### 启动服务

```bash
# 后端 (端口 8000)
cd backend
uvicorn app.main:app --reload

# 前端 (端口 5173)
cd frontend
npm run dev
```

### 访问应用

打开浏览器访问 http://127.0.0.1:5173

## 支持的 API 提供商

- Anthropic (Claude)
- OpenAI (ChatGPT)
- DeepSeek
- 小米 MiMo
- 硅基流动 (SiliconFlow)
- 火山引擎 (ByteDance)
- NVIDIA
- 智谱 (GLM)
- MiniMax
- Kimi (Moonshot)
- StepFun (阶跃星辰)
- 千问 (阿里云)
- Google Gemini
- 自定义 OpenAI 兼容接口

## 技术栈

- **后端**: FastAPI + SQLModel + SQLite + Playwright
- **前端**: React + Vite
- **AI**: 支持多种 OpenAI 兼容 API

## License

MIT
