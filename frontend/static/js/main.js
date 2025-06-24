// 主要应用逻辑
class DoodleApp {
    constructor() {
        this.currentTaskId = null;
        this.isProcessing = false;
        this.init();
    }

    init() {
        this.bindEvents();
        this.initializeUI();
    }

    bindEvents() {
        // 文件上传相关事件
        const imageInput = document.getElementById('imageInput');
        const uploadForm = document.getElementById('uploadForm');
        const removeFileBtn = document.getElementById('removeFile');

        imageInput.addEventListener('change', this.handleFileSelect.bind(this));
        uploadForm.addEventListener('submit', this.handleFormSubmit.bind(this));
        removeFileBtn.addEventListener('click', this.removeFile.bind(this));

        // 拖拽上传支持
        const uploadLabel = document.querySelector('.file-upload-label');
        uploadLabel.addEventListener('dragover', this.handleDragOver.bind(this));
        uploadLabel.addEventListener('drop', this.handleDrop.bind(this));
    }

    initializeUI() {
        this.updateSubmitButton();
    }

    // 文件选择处理
    handleFileSelect(event) {
        const file = event.target.files[0];
        if (file) {
            this.displayFilePreview(file);
            this.updateSubmitButton();
        }
    }

    // 显示文件预览
    displayFilePreview(file) {
        const preview = document.getElementById('filePreview');
        const previewImage = document.getElementById('previewImage');
        const fileName = document.getElementById('fileName');
        const uploadLabel = document.querySelector('.file-upload-label');

        // 创建文件URL并显示预览
        const fileURL = URL.createObjectURL(file);
        previewImage.src = fileURL;
        fileName.textContent = file.name;

        // 隐藏上传区域，显示预览
        uploadLabel.style.display = 'none';
        preview.style.display = 'flex';
    }

    // 移除文件
    removeFile() {
        const imageInput = document.getElementById('imageInput');
        const preview = document.getElementById('filePreview');
        const uploadLabel = document.querySelector('.file-upload-label');
        const previewImage = document.getElementById('previewImage');

        imageInput.value = '';
        preview.style.display = 'none';
        uploadLabel.style.display = 'flex';
        
        // 释放预览图片的内存
        if (previewImage.src) {
            URL.revokeObjectURL(previewImage.src);
            previewImage.src = '';
        }

        this.updateSubmitButton();
    }

    // 拖拽处理
    handleDragOver(event) {
        event.preventDefault();
        event.stopPropagation();
        event.currentTarget.classList.add('drag-over');
    }

    handleDrop(event) {
        event.preventDefault();
        event.stopPropagation();
        event.currentTarget.classList.remove('drag-over');

        const files = event.dataTransfer.files;
        if (files.length > 0) {
            const file = files[0];
            if (file.type.startsWith('image/')) {
                document.getElementById('imageInput').files = files;
                this.displayFilePreview(file);
                this.updateSubmitButton();
            } else {
                this.showToast('请上传图片文件', 'error');
            }
        }
    }

    // 更新提交按钮状态
    updateSubmitButton() {
        const submitBtn = document.getElementById('submitBtn');
        const imageInput = document.getElementById('imageInput');
        
        submitBtn.disabled = !imageInput.files || imageInput.files.length === 0 || this.isProcessing;
    }

    // 表单提交处理
    async handleFormSubmit(event) {
        event.preventDefault();
        
        if (this.isProcessing) {
            return;
        }

        const imageInput = document.getElementById('imageInput');
        const descriptionInput = document.getElementById('descriptionInput');

        if (!imageInput.files || imageInput.files.length === 0) {
            this.showToast('请先选择一张图片', 'error');
            return;
        }

        const formData = new FormData();
        formData.append('image', imageInput.files[0]);
        formData.append('description', descriptionInput.value.trim());

        this.isProcessing = true;
        this.updateSubmitButton();
        this.showLoading();

        try {
            // 第一步：上传文件
            const uploadResponse = await this.uploadFile(formData);
            if (!uploadResponse.success) {
                throw new Error(uploadResponse.detail || '上传失败');
            }

            this.currentTaskId = uploadResponse.task_id;
            this.addUserMessage(imageInput.files[0], descriptionInput.value.trim());

            // 第二步：开始处理
            await this.processImage(this.currentTaskId);

        } catch (error) {
            this.hideLoading();
            this.showToast(`处理失败: ${error.message}`, 'error');
            this.addErrorMessage(error.message);
        } finally {
            this.isProcessing = false;
            this.updateSubmitButton();
        }
    }

    // 上传文件
    async uploadFile(formData) {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || '上传失败');
        }

        return await response.json();
    }

    // 处理图片
    async processImage(taskId) {
        try {
            // 发起处理请求
            const processResponse = await fetch(`/api/process/${taskId}`, {
                method: 'POST'
            });

            if (!processResponse.ok) {
                const error = await processResponse.json();
                throw new Error(error.detail || '处理失败');
            }

            const result = await processResponse.json();
            this.hideLoading();
            this.addAssistantMessage(result);

        } catch (error) {
            this.hideLoading();
            throw error;
        }
    }

    // 显示加载状态
    showLoading() {
        const modal = document.getElementById('progressModal');
        const submitBtn = document.getElementById('submitBtn');
        
        modal.style.display = 'flex';
        
        // 更新按钮状态
        submitBtn.querySelector('.btn-text').style.display = 'none';
        submitBtn.querySelector('.btn-loading').style.display = 'flex';

        // 模拟进度更新
        this.simulateProgress();
    }

    // 隐藏加载状态
    hideLoading() {
        const modal = document.getElementById('progressModal');
        const submitBtn = document.getElementById('submitBtn');
        
        modal.style.display = 'none';
        
        // 恢复按钮状态
        submitBtn.querySelector('.btn-text').style.display = 'inline';
        submitBtn.querySelector('.btn-loading').style.display = 'none';
    }

    // 模拟进度更新
    simulateProgress() {
        const progressFill = document.getElementById('progressFill');
        const progressText = document.getElementById('progressText');
        const steps = ['step1', 'step2', 'step3'];
        
        let progress = 0;
        let stepIndex = 0;
        
        const progressInterval = setInterval(() => {
            if (!this.isProcessing) {
                clearInterval(progressInterval);
                progressFill.style.width = '100%';
                progressText.textContent = '处理完成！';
                
                // 标记所有步骤为完成
                steps.forEach(stepId => {
                    document.getElementById(stepId).classList.add('completed');
                });
                return;
            }

            progress += Math.random() * 15;
            if (progress > 95) progress = 95;
            
            progressFill.style.width = `${progress}%`;
            
            // 更新步骤状态
            if (progress > 30 && stepIndex < 1) {
                document.getElementById('step1').classList.add('completed');
                document.getElementById('step2').classList.add('active');
                progressText.textContent = '正在美化插画...';
                stepIndex = 1;
            } else if (progress > 70 && stepIndex < 2) {
                document.getElementById('step2').classList.add('completed');
                document.getElementById('step3').classList.add('active');
                progressText.textContent = '正在生成最终结果...';
                stepIndex = 2;
            }
        }, 1000);
    }

    // 添加用户消息
    addUserMessage(file, description) {
        const chatMessages = document.getElementById('chatMessages');
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message user-message';
        
        const fileURL = URL.createObjectURL(file);
        
        messageDiv.innerHTML = `
            <div class="message-content">
                <div class="uploaded-image">
                    <img src="${fileURL}" alt="上传的涂鸦" style="max-width: 200px; border-radius: 8px; margin-bottom: 1rem;">
                </div>
                <p><strong>上传的图片：</strong>${file.name}</p>
                ${description ? `<p><strong>描述：</strong>${description}</p>` : ''}
                <p>请帮我将这幅涂鸦美化为绘本级插画！</p>
            </div>
        `;
        
        chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }

    // 添加助手消息
    addAssistantMessage(result) {
        const chatMessages = document.getElementById('chatMessages');
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message assistant-message';
        
        let content = `
            <div class="message-content">
                <h3>✨ 涂鸦美化完成！</h3>
                <div class="result-text">${result.result}</div>
        `;
        
        // 如果有生成的图片，显示对比
        if (result.enhanced_image_path) {
            content += `
                <div class="result-images">
                    <div class="image-card">
                        <h4>美化后的插画</h4>
                        <img src="${result.enhanced_image_path}" alt="美化后的插画">
                        <br>
                        <button onclick="downloadImage('${result.task_id}')" class="download-btn">
                            📥 下载插画
                        </button>
                    </div>
                </div>
            `;
        }
        
        content += `</div>`;
        messageDiv.innerHTML = content;
        
        chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }

    // 添加错误消息
    addErrorMessage(error) {
        const chatMessages = document.getElementById('chatMessages');
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message assistant-message';
        
        messageDiv.innerHTML = `
            <div class="message-content" style="border-left: 4px solid #ff6b6b;">
                <h3>❌ 处理失败</h3>
                <p>很抱歉，处理过程中出现了错误：</p>
                <div class="result-text" style="background: #fff5f5; border-left-color: #ff6b6b;">
                    ${error}
                </div>
                <p>请检查以下项目：</p>
                <ul style="margin: 1rem 0; padding-left: 1.5rem;">
                    <li>确保已配置 DEEPSEEK_API_KEY</li>
                    <li>确保已配置 REPLICATE_API_TOKEN</li>
                    <li>检查网络连接是否正常</li>
                    <li>尝试重新上传图片</li>
                </ul>
            </div>
        `;
        
        chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }

    // 滚动到底部
    scrollToBottom() {
        const chatMessages = document.getElementById('chatMessages');
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // 显示提示信息
    showToast(message, type = 'info') {
        // 创建或获取提示框
        let toast = document.getElementById('toast');
        if (!toast) {
            toast = document.createElement('div');
            toast.id = 'toast';
            toast.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 1rem 1.5rem;
                border-radius: 8px;
                color: white;
                font-weight: 600;
                z-index: 10000;
                transform: translateX(400px);
                transition: transform 0.3s ease;
            `;
            document.body.appendChild(toast);
        }

        // 设置样式和内容
        const colors = {
            info: '#667eea',
            success: '#28a745',
            error: '#ff6b6b',
            warning: '#ffa726'
        };
        
        toast.style.background = colors[type] || colors.info;
        toast.textContent = message;
        toast.style.transform = 'translateX(0)';

        // 自动隐藏
        setTimeout(() => {
            toast.style.transform = 'translateX(400px)';
        }, 3000);
    }
}

// 下载图片函数
function downloadImage(taskId) {
    const downloadUrl = `/api/download/${taskId}`;
    
    // 创建一个隐藏的链接来触发下载
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = `enhanced_doodle_${taskId}.jpg`;
    link.style.display = 'none';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// 初始化应用
document.addEventListener('DOMContentLoaded', () => {
    new DoodleApp();
});

// 添加拖拽样式
const style = document.createElement('style');
style.textContent = `
    .file-upload-label.drag-over {
        border-color: #28a745 !important;
        background: linear-gradient(135deg, #f0fff4, #e8f5e8) !important;
        transform: scale(1.02) !important;
    }
`;
document.head.appendChild(style); 