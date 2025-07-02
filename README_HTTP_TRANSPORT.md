# FractFlow HTTP Transport Mode

FractFlow 现已支持 HTTP 传输模式，允许工具通过网络提供服务，而不仅仅是本地子进程执行。

## 功能概述

HTTP 传输模式提供了以下优势：

- **网络访问**：工具可以通过 HTTP 端点访问，支持远程调用
- **向后兼容**：现有的 STDIO 工具继续正常工作
- **流式支持**：符合 MCP Streamable HTTP 协议规范
- **会话管理**：支持有状态的 MCP 会话
- **自动端口分配**：智能端口管理，避免冲突

## 快速开始

### 1. 创建 HTTP 工具

```python
from FractFlow.tool_template import ToolTemplate

class MyHttpTool(ToolTemplate):
    # 必需属性
    SYSTEM_PROMPT = "你是一个有用的助手..."
    TOOL_DESCRIPTION = "这个工具通过HTTP提供服务..."
    
    # HTTP 传输配置
    TRANSPORT_MODE = "http"  # 启用 HTTP 模式
    HTTP_PORT = 8001        # 指定端口
    HTTP_HOST = "127.0.0.1" # 绑定地址

if __name__ == "__main__":
    MyHttpTool.main()
```

### 2. 运行 HTTP 工具

```bash
python my_http_tool.py
```

工具将启动 HTTP 服务器：
```
Starting MyHttpTool HTTP server at http://127.0.0.1:8001
INFO: Uvicorn running on http://127.0.0.1:8001 (Press CTRL+C to quit)
```

### 3. 测试连接

使用 curl 测试 MCP 协议：

```bash
# 初始化连接
curl -X POST http://127.0.0.1:8001/mcp/ \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{}},"jsonrpc":"2.0","id":0}'
```

## 配置选项

### 基本配置

```python
class MyTool(ToolTemplate):
    TRANSPORT_MODE = "http"     # "stdio" | "http"
    HTTP_PORT = 8001           # 端口号，None 表示自动分配
    HTTP_HOST = "127.0.0.1"    # 绑定地址
```

### 自动端口分配

```python
class MyTool(ToolTemplate):
    TRANSPORT_MODE = "http"
    HTTP_PORT = None          # 系统自动分配可用端口
```

### STDIO 模式（默认）

```python
class MyTool(ToolTemplate):
    # TRANSPORT_MODE = "stdio"  # 默认值，可省略
    SYSTEM_PROMPT = "..."
    TOOL_DESCRIPTION = "..."
```

## 在 Agent 中使用 HTTP 工具

目前，Agent 仍通过文件路径注册工具，工具的传输模式由工具本身的配置决定：

```python
from FractFlow.agent import Agent
from FractFlow.infra.config import ConfigManager

# 创建配置和 Agent
config = ConfigManager()
agent = Agent(config=config, name='my_agent')

# 添加工具（传输模式由工具类的 TRANSPORT_MODE 决定）
agent.add_tool("./my_http_tool.py", "my_tool")

# 初始化并使用
await agent.initialize()
result = await agent.process_query("执行某个操作")
```

## 协议支持

支持完整的 MCP Streamable HTTP 协议：

- **POST /mcp/**: 发送 JSON-RPC 请求
- **GET /mcp/**: 建立 SSE 连接（如果需要）
- **会话管理**: 自动处理 session ID
- **流式响应**: 支持 Server-Sent Events
- **错误处理**: 标准 JSON-RPC 错误响应

## 网络安全

HTTP 模式默认只绑定到 localhost (127.0.0.1)，确保安全性：

```python
HTTP_HOST = "127.0.0.1"  # 仅本地访问（推荐）
# HTTP_HOST = "0.0.0.0"  # 允许外部访问（需谨慎）
```

## 故障排除

### 端口冲突

```
ERROR: [Errno 48] error while attempting to bind on address ('127.0.0.1', 8001): address already in use
```

解决方案：
1. 更改 `HTTP_PORT` 为其他值
2. 或设置 `HTTP_PORT = None` 使用自动分配

### 连接被拒绝

确保：
1. HTTP 服务器正在运行
2. 端口号正确
3. 使用正确的协议头

### MCP 协议错误

```json
{
  "error": {
    "code": -32600,
    "message": "Not Acceptable: Client must accept both application/json and text/event-stream"
  }
}
```

解决方案：使用正确的 Accept 头：
```
Accept: application/json, text/event-stream
```

## 协议对比

| 特性 | STDIO 模式 | HTTP 模式 |
|------|------------|-----------|
| 网络访问 | ❌ | ✅ |
| 并发连接 | 一对一 | 多客户端 |
| 会话管理 | 进程生命周期 | HTTP 会话 |
| 资源占用 | 低 | 中等 |
| 安全性 | 高（本地） | 需配置 |
| 调试便利性 | 高 | 中等 |

## 最佳实践

1. **开发阶段**：使用 STDIO 模式便于调试
2. **生产环境**：考虑使用 HTTP 模式支持并发
3. **安全配置**：生产环境建议配置认证和 HTTPS
4. **端口管理**：使用自动端口分配避免冲突
5. **错误处理**：让真实错误信息透传，便于调试

## 未来规划

- 添加 HTTP 客户端连接支持到 MCPClientPool
- 支持认证和授权
- 支持 HTTPS 传输
- 混合模式工具（同时支持 STDIO 和 HTTP） 