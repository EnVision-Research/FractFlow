# 🎨 儿童涂鸦美化Web应用 - 前端项目

基于FastAPI + HTML的前后端分离架构，提供现代化的儿童涂鸦美化服务。

## 🌟 特性

- **🏗️ 前后端分离**：FastAPI后端 + 原生HTML/CSS/JS前端
- **🎨 现代化界面**：ChatGPT风格的对话式交互
- **📱 响应式设计**：支持桌面和移动设备
- **⚡ 实时进度**：显示处理进度和状态
- **🔄 拖拽上传**：支持拖拽文件上传
- **📥 结果下载**：直接下载美化后的插画

## 📁 项目结构

```
frontend/
├── app.py              # FastAPI 后端服务器
├── run.py              # 启动脚本
├── requirements.txt    # Python 依赖
├── README.md          # 项目说明
├── templates/         # HTML 模板
│   └── index.html     # 主页面
├── static/           # 静态资源
│   ├── css/
│   │   └── style.css  # 样式文件
│   └── js/
│       └── main.js    # JavaScript 逻辑
└── uploads/          # 上传文件存储
```

## 🚀 快速开始

### 1. 安装依赖

在项目根目录下：
```bash
# 安装前端项目依赖
cd frontend
pip install -r requirements.txt
```

### 2. 配置环境

确保项目根目录的 `.env` 文件包含：
```env
DEEPSEEK_API_KEY=your_deepseek_api_key_here
REPLICATE_API_TOKEN=your_replicate_api_token_here
```

### 3. 启动应用

```bash
# 方式1：使用启动脚本
python run.py

# 方式2：直接运行FastAPI
python app.py

# 方式3：使用uvicorn命令
uvicorn app:app --host 0.0.0.0 --port 8000
```

### 4. 访问应用

- **前端界面**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **OpenAPI规范**: http://localhost:8000/redoc

## 🛠️ API 端点

### `GET /`
主页面，返回HTML界面

### `POST /api/upload`
上传图片文件
- **参数**: 
  - `image`: 图片文件 (multipart/form-data)
  - `description`: 可选描述 (form field)
- **返回**: `{success: true, task_id: "uuid", message: "上传成功"}`

### `POST /api/process/{task_id}`
处理涂鸦美化任务
- **参数**: `task_id` (路径参数)
- **返回**: 处理结果和生成的图片路径

### `GET /api/status/{task_id}`
获取任务处理状态
- **参数**: `task_id` (路径参数)
- **返回**: 任务状态信息

### `GET /health`
健康检查端点

## 🎯 使用流程

1. **上传图片**: 拖拽或点击选择儿童涂鸦图片
2. **添加描述**: 可选地描述画作内容
3. **开始处理**: 点击"开始美化"按钮
4. **查看进度**: 实时显示AI处理进度
5. **获取结果**: 查看美化后的插画并下载

## 🔧 技术栈

- **后端**: FastAPI, Python 3.10+
- **前端**: HTML5, CSS3, Vanilla JavaScript
- **AI集成**: DoodleImageGenerator (GPT-4o + Flux Kontext Pro)
- **部署**: Uvicorn ASGI服务器

## 🐛 故障排除

### 常见问题

1. **导入错误**
   ```bash
   # 检查DoodleImageGenerator导入
   python -c "from tools.composite.doodle_img_generator import DoodleImageGenerator"
   ```

2. **API密钥问题**
   ```bash
   # 检查环境变量
   python -c "import os; print('DEEPSEEK_API_KEY:', bool(os.getenv('DEEPSEEK_API_KEY')))"
   python -c "import os; print('REPLICATE_API_TOKEN:', bool(os.getenv('REPLICATE_API_TOKEN')))"
   ```

3. **端口占用**
   ```bash
   # 检查端口使用情况
   lsof -i :8000
   
   # 或使用其他端口
   uvicorn app:app --port 8001
   ```

### 调试模式

启用详细日志：
```bash
python app.py --log-level debug
```

## 🔄 开发指南

### 修改前端界面
编辑 `templates/index.html` 和 `static/css/style.css`

### 修改JavaScript逻辑
编辑 `static/js/main.js`

### 修改API逻辑
编辑 `app.py`

### 热重载开发
```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

## 🚀 部署建议

### 生产环境
```bash
# 使用Gunicorn + Uvicorn
pip install gunicorn
gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Docker部署
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 📝 更新日志

- **v1.0.0**: 初始版本，前后端分离架构
- 基础功能：图片上传、AI处理、结果展示
- 现代化UI设计，响应式布局
- 实时进度显示和错误处理

---

如有问题，请参考项目根目录的主要README文档或提交Issue。 