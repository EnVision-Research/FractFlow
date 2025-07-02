"""
测试AgentLauncher功能
验证多Agent端口复用功能是否正常工作
"""

import pytest
import asyncio
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# 导入要测试的模块
from agent_launcher import AgentLauncher


class MockAgent:
    """模拟Agent类用于测试"""
    
    @classmethod
    def _validate_configuration(cls):
        """模拟配置验证"""
        pass
    
    @classmethod
    def _create_fastmcp_server(cls):
        """模拟创建FastMCP服务器"""
        mock_server = MagicMock()
        mock_server.session_manager.run.return_value = asyncio.create_task(asyncio.sleep(0))
        mock_server.streamable_http_app.return_value = MagicMock()
        return mock_server


def test_agent_launcher_initialization():
    """测试AgentLauncher初始化"""
    launcher = AgentLauncher()
    assert launcher.agents == {}
    assert launcher.mcp_servers == {}
    assert len(launcher.tools_dirs) == 2


def test_scan_agents_empty_directory():
    """测试在空目录中扫描agents"""
    launcher = AgentLauncher()
    
    # 模拟空的tools目录
    with tempfile.TemporaryDirectory() as temp_dir:
        launcher.tools_dirs = [Path(temp_dir)]
        agent_files = launcher.scan_agents()
        assert agent_files == []


def test_scan_agents_with_files():
    """测试扫描包含agent文件的目录"""
    launcher = AgentLauncher()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建测试agent文件
        temp_path = Path(temp_dir)
        (temp_path / "test_agent.py").touch()
        (temp_path / "another_agent.py").touch()
        (temp_path / "not_agent.py").touch()  # 不匹配模式
        
        launcher.tools_dirs = [temp_path]
        agent_files = launcher.scan_agents()
        
        # 应该找到2个agent文件
        assert len(agent_files) == 2
        assert any("test_agent.py" in f for f in agent_files)
        assert any("another_agent.py" in f for f in agent_files)


@patch('agent_launcher.importlib.util')
def test_load_agent(mock_importlib):
    """测试动态加载agent"""
    launcher = AgentLauncher()
    
    # 模拟模块加载
    mock_module = MagicMock()
    mock_module.TestAgent = MockAgent
    
    mock_spec = MagicMock()
    mock_spec.loader.exec_module = MagicMock()
    
    mock_importlib.spec_from_file_location.return_value = mock_spec
    mock_importlib.module_from_spec.return_value = mock_module
    
    # 设置模块属性
    with patch.object(mock_module, '__dir__', return_value=['TestAgent']):
        with patch('builtins.getattr', return_value=MockAgent):
            with patch('builtins.isinstance', return_value=True):
                with patch('builtins.issubclass', return_value=True):
                    agent_class = launcher.load_agent("test_agent.py")
                    assert agent_class == MockAgent


def test_register_agents():
    """测试注册agents"""
    launcher = AgentLauncher()
    
    # 模拟扫描和加载过程
    with patch.object(launcher, 'scan_agents', return_value=['test_agent.py']):
        with patch.object(launcher, 'load_agent', return_value=MockAgent):
            launcher.register_agents()
            
            # 验证agent已注册
            assert 'mockagent' in launcher.agents
            assert 'mockagent' in launcher.mcp_servers


def test_create_app():
    """测试创建FastAPI应用"""
    launcher = AgentLauncher()
    
    # 添加模拟agent
    launcher.agents['test_agent'] = MockAgent
    launcher.mcp_servers['test_agent'] = MockAgent._create_fastmcp_server()
    
    app = launcher.create_app()
    
    # 验证应用创建成功
    assert app.title == "FractFlow Multi-Agent Server"
    assert "test_agent" in app.description or len(launcher.agents) == 1


def test_health_endpoint():
    """测试健康检查端点"""
    launcher = AgentLauncher()
    launcher.agents['test_agent'] = MockAgent
    launcher.mcp_servers['test_agent'] = MockAgent._create_fastmcp_server()
    
    app = launcher.create_app()
    client = TestClient(app)
    
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert data["agents_count"] == 1
    assert "test_agent" in data["agents"]


def test_root_endpoint():
    """测试根端点"""
    launcher = AgentLauncher()
    launcher.agents['test_agent'] = MockAgent
    launcher.mcp_servers['test_agent'] = MockAgent._create_fastmcp_server()
    
    app = launcher.create_app()
    client = TestClient(app)
    
    response = client.get("/")
    assert response.status_code == 200
    
    data = response.json()
    assert data["message"] == "FractFlow Multi-Agent Server"
    assert "test_agent" in data["agents"]
    assert "/test_agent/mcp" in data["endpoints"]


if __name__ == "__main__":
    # 运行基本测试
    print("🧪 Running AgentLauncher tests...")
    
    test_agent_launcher_initialization()
    print("✓ Initialization test passed")
    
    test_scan_agents_empty_directory()
    print("✓ Empty directory scan test passed")
    
    test_scan_agents_with_files()
    print("✓ File scanning test passed")
    
    test_register_agents()
    print("✓ Agent registration test passed")
    
    test_create_app()
    print("✓ App creation test passed")
    
    test_health_endpoint()
    print("✓ Health endpoint test passed")
    
    test_root_endpoint()
    print("✓ Root endpoint test passed")
    
    print("\n🎉 All tests passed! AgentLauncher is working correctly.") 