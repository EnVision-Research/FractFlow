#!/usr/bin/env python3
"""
FastAPI 后端服务器
提供儿童涂鸦美化API服务
"""

import os
import sys
import asyncio
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
import uvicorn

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

# 导入DoodleImageGenerator
try:
    from tools.composite.doodle_img_generator import DoodleImageGenerator
except ImportError as e:
    print(f"❌ 无法导入DoodleImageGenerator: {e}")
    sys.exit(1)

# 创建FastAPI应用
app = FastAPI(
    title="儿童涂鸦美化API",
    description="将儿童涂鸦转换为精美绘本插画",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置静态文件和模板
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

# 配置数据文件服务（用于访问上传和生成的图片）
data_dir = "data"
if os.path.exists(data_dir):
    app.mount("/data", StaticFiles(directory=data_dir), name="static_data")

templates = Jinja2Templates(directory="frontend/templates")

# 创建上传和输出目录
UPLOAD_DIR = Path("data/uploads")
OUTPUT_DIR = Path("data/outputs")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 存储处理状态
processing_status = {}

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """主页面"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/favicon.ico")
async def favicon():
    """返回favicon图标，避免404错误"""
    from fastapi.responses import Response
    # 返回一个简单的emoji图标作为favicon
    favicon_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y=".9em" font-size="90">🎨</text></svg>"""
    return Response(content=favicon_content, media_type="image/svg+xml")

@app.post("/api/upload")
async def upload_image(
    image: UploadFile = File(...),
    description: str = Form(default="")
):
    """
    上传图片并开始处理
    """
    try:
        # 验证文件类型
        if not image.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="请上传图片文件")
        
        # 生成唯一的任务ID
        task_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 创建task_id子目录
        task_upload_dir = UPLOAD_DIR / task_id
        task_upload_dir.mkdir(exist_ok=True)
        
        # 保存上传的文件
        file_extension = Path(image.filename).suffix
        filename = f"original{file_extension}"
        file_path = task_upload_dir / filename
        
        content = await image.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        # 初始化处理状态
        processing_status[task_id] = {
            "status": "uploaded",
            "progress": 10,
            "message": "图片上传成功",
            "image_path": str(file_path),
            "description": description,
            "result": None,
            "error": None
        }
        
        return JSONResponse({
            "success": True,
            "task_id": task_id,
            "message": "图片上传成功",
            "filename": filename
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")

@app.post("/api/process/{task_id}")
async def process_doodle(task_id: str):
    """
    处理涂鸦美化任务
    """
    try:
        if task_id not in processing_status:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        status = processing_status[task_id]
        
        # 更新状态：开始处理
        status["status"] = "processing"
        status["progress"] = 20
        status["message"] = "AI正在分析涂鸦..."
        
        # 构建查询字符串
        image_path = status["image_path"]
        description = status["description"]
        
        # 创建输出目录和路径
        task_output_dir = OUTPUT_DIR / task_id
        task_output_dir.mkdir(exist_ok=True)
        output_path = task_output_dir / f"{task_id}.jpg"
        
        if description.strip():
            query = f"美化涂鸦：image_path='{image_path}' output_path='{output_path}' description='{description}'"
        else:
            query = f"美化涂鸦：image_path='{image_path}' output_path='{output_path}'"
        
        # 更新进度
        status["progress"] = 40
        status["message"] = "正在调用DoodleImageGenerator..."
        
        # 创建DoodleImageGenerator实例并处理
        generator = DoodleImageGenerator()
        result = await generator._mcp_tool_function(query)
        
        # 更新状态：处理完成
        status["status"] = "completed"
        status["progress"] = 100
        status["message"] = "处理完成"
        status["result"] = result
        
        # 直接定位生成的图片路径
        enhanced_image_path = None
        expected_output_path = OUTPUT_DIR / task_id / f"{task_id}.jpg"
        if expected_output_path.exists():
            # 使用/data路径来访问
            relative_path = str(expected_output_path).replace(os.sep, '/')
            enhanced_image_path = f"/{relative_path}"
        
        return JSONResponse({
            "success": True,
            "task_id": task_id,
            "result": result,
            "enhanced_image_path": enhanced_image_path,
            "message": "处理完成"
        })
        
    except Exception as e:
        # 更新状态：处理失败
        if task_id in processing_status:
            processing_status[task_id]["status"] = "error"
            processing_status[task_id]["progress"] = 0
            processing_status[task_id]["message"] = f"处理失败: {str(e)}"
            processing_status[task_id]["error"] = str(e)
        
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")

@app.get("/api/status/{task_id}")
async def get_status(task_id: str):
    """
    获取任务处理状态
    """
    if task_id not in processing_status:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return JSONResponse(processing_status[task_id])

@app.get("/api/download/{task_id}")
async def download_result(task_id: str):
    """
    下载处理结果
    """
    if task_id not in processing_status:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    status = processing_status[task_id]
    if status["status"] != "completed":
        raise HTTPException(status_code=400, detail="任务未完成")
    
    # 直接定位生成的图片文件
    enhanced_image_path = OUTPUT_DIR / task_id / f"{task_id}.jpg"
    
    if not enhanced_image_path.exists():
        raise HTTPException(status_code=404, detail="生成的图片文件未找到")
    
    # 返回文件下载
    from fastapi.responses import FileResponse
    return FileResponse(
        path=str(enhanced_image_path),
        filename=f"enhanced_doodle_{task_id}.jpg",
        media_type='image/jpeg'
    )

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "doodle_image_generator"}

if __name__ == "__main__":
    print("🎨 启动儿童涂鸦美化API服务器...")
    print("🌐 服务地址: http://localhost:8000")
    print("📚 API文档: http://localhost:8000/docs")
    print("⏹️  按 Ctrl+C 停止服务")
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # 避免文件监控问题
        log_level="info"
    ) 