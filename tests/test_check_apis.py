"""单元测试文件 for check_apis.py"""
import pytest
import json
import csv
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path
from dataclasses import asdict

# 添加 scripts 目录到 Python 路径
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.check_apis import APICheckResult, APIConfig, APIChecker, CacheManager, DataReader, ReportGenerator
from dataclasses import asdict


class TestAPIConfig:
    """测试 APIConfig 数据类"""
    
    def test_api_config_creation(self):
        """测试 APIConfig 对象创建"""
        api_config = APIConfig(
            name="Test API",
            link="https://api.example.com",
            description="Test Description",
            auth="oauth",
            https=True,
            cors="yes"
        )
        
        assert api_config.name == "Test API"
        assert api_config.link == "https://api.example.com"
        assert api_config.description == "Test Description"
        assert api_config.auth == "oauth"
        assert api_config.https == True
        assert api_config.cors == "yes"


class TestDataReader:
    """测试 DataReader 类"""
    
    def test_read_json(self, tmp_path):
        """测试读取 JSON 文件"""
        # 创建临时 JSON 文件
        data = [{
            "name": "Test API",
            "link": "https://api.example.com",
            "description": "Test Description",
            "auth": "",
            "cors": "yes",
            "category": "Test"
        }]
        
        json_file = tmp_path / "test_apis.json"
        with open(json_file, 'w') as f:
            json.dump(data, f)
        
        api_configs = DataReader.read(str(json_file))
        
        assert len(api_configs) == 1
        assert api_configs[0].name == "Test API"
        assert api_configs[0].link == "https://api.example.com"
    
    def test_read_csv(self, tmp_path):
        """测试读取 CSV 文件"""
        # 创建临时 CSV 文件
        csv_file = tmp_path / "test_apis.csv"
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["name", "link", "description", "auth", "https", "cors"])
            writer.writerow(["Test API", "https://api.example.com", "Test Description", "", "True", "yes"])
        
        api_configs = DataReader.read(str(csv_file))
        
        assert len(api_configs) == 1
        assert api_configs[0].name == "Test API"
        assert api_configs[0].link == "https://api.example.com"
    
    def test_invalid_file_extension(self):
        """测试无效文件扩展名"""
        with pytest.raises(ValueError):
            DataReader.read("test.txt")


class TestReportGenerator:
    """测试 ReportGenerator 类"""
    
    def test_generate_json(self, tmp_path):
        """测试生成 JSON 报告"""
        # 创建测试结果
        results = [
            APICheckResult(
                name="Test API",
                link="https://api.example.com",
                status_code=200,
                response_time=150.5,
                error=None,
                checked_at=datetime.now().isoformat(),
                from_cache=False
            )
        ]
        
        output_file = tmp_path / "report.json"
        ReportGenerator.generate_json(results, str(output_file))
        
        # 验证文件生成
        assert output_file.exists()
        
        # 验证内容
        with open(output_file, 'r') as f:
            data = json.load(f)
            assert len(data) == 1
            assert data[0]["name"] == "Test API"
            assert data[0]["status_code"] == 200
            assert data[0]["http_status"] == 200  # 验收标准字段
            assert data[0]["response_time_ms"] == 150.5  # 验收标准字段
            assert data[0]["status"] == "success"  # 验收标准字段
    
    def test_generate_csv(self, tmp_path):
        """测试生成 CSV 报告"""
        # 创建测试结果
        results = [
            APICheckResult(
                name="Test API",
                link="https://api.example.com",
                status_code=200,
                response_time=150.5,
                error=None,
                checked_at=datetime.now().isoformat(),
                from_cache=False
            )
        ]
        
        output_file = tmp_path / "report.csv"
        ReportGenerator.generate_csv(results, str(output_file))
        
        # 验证文件生成
        assert output_file.exists()
        
        # 验证内容
        with open(output_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            assert rows[0]["name"] == "Test API"
            assert rows[0]["status_code"] == "200"
            assert rows[0]["http_status"] == "200"  # 验收标准字段
            assert rows[0]["response_time_ms"] == "150.5"  # 验收标准字段
            assert rows[0]["status"] == "success"  # 验收标准字段
    
    def test_generate_no_results(self, tmp_path):
        """测试生成空报告"""
        output_file = tmp_path / "report.json"
        ReportGenerator.generate_json([], str(output_file))
        # 应该生成空文件但不会崩溃


class TestCacheManager:
    """测试 CacheManager 类"""
    
    def test_cache_operations(self, tmp_path):
        """测试缓存的基本操作"""
        cache_dir = tmp_path / "cache"
        # 修复：正确设置cache_ttl和cache_dir参数
        cache_manager = CacheManager(cache_ttl=3600, cache_dir=str(cache_dir))
        
        # 测试缓存不存在
        result = cache_manager.get("https://api.example.com")
        assert result is None
        
        # 测试缓存存储
        data = {
            "name": "Test API",
            "link": "https://api.example.com",
            "status_code": 200,
            "response_time": 150.5,
            "error": None,
            "checked_at": datetime.now().isoformat()
        }
        cache_manager.set("https://api.example.com", data)
        
        # 测试缓存获取
        result = cache_manager.get("https://api.example.com")
        assert result is not None
        assert result["name"] == "Test API"
        
        # 测试缓存清理
        cache_manager.clear_all()
        result = cache_manager.get("https://api.example.com")
        assert result is None


class TestAPIChecker:
    """测试 APIChecker 类"""
    
    @pytest.mark.asyncio
    async def test_check_api_config_success(self):
        """测试 APIConfig 检查成功的情况"""
        # 创建 APIConfig 对象
        api_config = APIConfig(
            name="Test API",
            link="https://api.example.com",
            description="Test Description",
            auth="",
            cors="yes"
        )
        
        # 模拟 aiohttp ClientSession
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="")
        # 修复: 确保 mock_response 有 __aenter__ 和 __aexit__ 方法
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        mock_session.get = AsyncMock(return_value=mock_response)
        # 修复: 确保 mock_session 作为上下文管理器返回自身
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        # 创建 APIChecker
        checker = APIChecker(concurrency=10, timeout=5, retries=3, cache_ttl=3600, force_refresh=False)
        
        # 检查 APIConfig
        progress = asyncio.Queue()
        result = await checker._check_single_api(api_config, mock_session, progress)
        
        # 验证结果
        result_dict = asdict(result)
        assert result_dict["name"] == "Test API"
        assert result_dict["status_code"] == 200
        assert result_dict["error"] is None
        assert result_dict["from_cache"] == False
        assert result_dict["http_status"] == 200  # 验收标准字段
        assert result_dict["response_time_ms"] is not None  # 验收标准字段
        assert result_dict["status"] == "success"  # 验收标准字段
    
    @pytest.mark.asyncio
    async def test_check_api_config_timeout(self):
        """测试 APIConfig 超时的情况"""
        # 创建 APIConfig 对象
        api_config = APIConfig(
            name="Test API",
            link="https://api.example.com",
            description="Test Description",
            auth="",
            cors="yes"
        )
        
        # 模拟超时异常
        mock_session = AsyncMock()
        mock_session.get = AsyncMock(side_effect=asyncio.TimeoutError)
        # 修复: 确保 mock_session 作为上下文管理器返回自身
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        # 创建 APIChecker
        checker = APIChecker(concurrency=10, timeout=1, retries=3, cache_ttl=3600, force_refresh=False)
        
        # 检查 APIConfig
        progress = asyncio.Queue()
        result = await checker._check_single_api(api_config, mock_session, progress)
        
        # 验证结果
        result_dict = asdict(result)
        assert result_dict["name"] == "Test API"
        assert result_dict["status_code"] is None
        assert "timeout" in result_dict["error"].lower()
        assert result_dict["status"] == "timeout"  # 验收标准字段
    
    @pytest.mark.asyncio
    async def test_check_api_config_error(self):
        """测试 APIConfig 检查失败的情况"""
        # 创建 APIConfig 对象
        api_config = APIConfig(
            name="Test API",
            link="https://api.example.com",
            description="Test Description",
            auth="",
            cors="yes"
        )
        
        # 模拟 HTTP 错误
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.text = AsyncMock(return_value="")
        # 修复: 确保 mock_response 有 __aenter__ 和 __aexit__ 方法
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        mock_session.get = AsyncMock(return_value=mock_response)
        # 修复: 确保 mock_session 作为上下文管理器返回自身
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        # 创建 APIChecker
        checker = APIChecker(concurrency=10, timeout=5, retries=3, cache_ttl=3600, force_refresh=False)
        
        # 检查 APIConfig
        progress = asyncio.Queue()
        result = await checker._check_single_api(api_config, mock_session, progress)
        
        # 验证结果
        result_dict = asdict(result)
        assert result_dict["name"] == "Test API"
        assert result_dict["status_code"] == 500
        assert result_dict["error"] is None  # 非 2xx 但无错误信息
        assert result_dict["status"] == "error"  # 验收标准字段
    
    @pytest.mark.asyncio
    async def test_check_api_config_connection_error(self):
        """测试连接错误的情况"""
        # 创建 APIConfig 对象
        api_config = APIConfig(
            name="Test API",
            link="https://api.example.com",
            description="Test Description",
            auth="",
            cors="yes"
        )
        
        # 模拟连接错误
        mock_session = AsyncMock()
        mock_session.get = AsyncMock(side_effect=Exception("Connection refused"))
        
        # 创建 APIChecker
        checker = APIChecker(concurrency=10, timeout=5, retries=3, cache_ttl=3600, force_refresh=False)
        
        # 检查 APIConfig
        progress = asyncio.Queue()
        result = await checker._check_single_api(api_config, mock_session, progress)
        
        # 验证结果
        result_dict = asdict(result)
        assert result_dict["name"] == "Test API"
        assert result_dict["status_code"] is None
        assert "Connection refused" in result_dict["error"]
        assert result_dict["status"] == "error"  # 验收标准字段
    
    @pytest.mark.asyncio
    @patch('scripts.check_apis.CacheManager')
    async def test_check_api_config_from_cache(self, mock_cache_manager_class):
        """测试从缓存获取结果的情况"""
        # 创建 APIConfig 对象
        api_config = APIConfig(
            name="Test API",
            link="https://api.example.com",
            description="Test Description",
            auth="",
            cors="yes"
        )
        
        # 模拟缓存管理器
        mock_cache_manager = Mock()
        mock_cache_manager.get.return_value = {
            "name": "Test API",
            "link": "https://api.example.com",
            "status_code": 200,
            "response_time": 150.5,
            "error": None,
            "checked_at": datetime.now().isoformat(),
            "from_cache": True,
            "http_status": 200,
            "response_time_ms": 150.5,
            "status": "success"
        }
        mock_cache_manager_class.return_value = mock_cache_manager
        
        # 创建 APIChecker
        checker = APIChecker(concurrency=10, timeout=5, retries=3, cache_ttl=3600, force_refresh=False)
        
        # 检查 APIConfig（会使用缓存）
        progress = asyncio.Queue()
        result = await checker._check_single_api(api_config, None, progress)  # session 不会被使用
        
        # 验证结果
        result_dict = asdict(result)
        assert result_dict["name"] == "Test API"
        assert result_dict["status_code"] == 200
        assert result_dict["from_cache"] == True
        assert result_dict["http_status"] == 200  # 验收标准字段
        assert result_dict["response_time_ms"] == 150.5  # 验收标准字段
        assert result_dict["status"] == "success"  # 验收标准字段
    
    @pytest.mark.asyncio
    @patch('scripts.check_apis.CacheManager')
    async def test_check_api_config_force_refresh(self, mock_cache_manager_class):
        """测试强制刷新缓存的情况"""
        # 创建 APIConfig 对象
        api_config = APIConfig(
            name="Test API",
            link="https://api.example.com",
            description="Test Description",
            auth="",
            cors="yes"
        )
        
        # 模拟缓存管理器
        mock_cache_manager = Mock()
        mock_cache_manager.get.return_value = {
            "name": "Test API",
            "link": "https://api.example.com",
            "status_code": 200,
            "response_time": 150.5,
            "error": None,
            "checked_at": datetime.now().isoformat()
        }
        mock_cache_manager_class.return_value = mock_cache_manager
        
        # 创建 APIChecker 并强制刷新
        checker = APIChecker(concurrency=10, timeout=5, retries=3, cache_ttl=3600, force_refresh=True)
        
        # 模拟强制刷新缓存的情况
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="")
        # 修复: 确保 mock_response 有 __aenter__ 和 __aexit__ 方法
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        mock_session.get = AsyncMock(return_value=mock_response)
        
        # 检查 APIConfig（会忽略缓存，重新请求）
        progress = asyncio.Queue()
        result = await checker._check_single_api(api_config, mock_session, progress)
        
        # 验证结果
        result_dict = asdict(result)
        assert result_dict["name"] == "Test API"
        assert result_dict["from_cache"] == False  # 不使用缓存
    
    @pytest.mark.asyncio
    @patch('scripts.check_apis.aiohttp.ClientSession')
    async def test_check_api_configs_concurrently(self, mock_client_session_class):
        """测试并发检查多个 APIConfig"""
        # 创建多个 APIConfig 对象
        api_configs = [
            APIConfig(
                name=f"Test API {i}",
                link=f"https://api.example{i}.com",
                description="Test Description",
                auth="",
                cors="yes"
            )
            for i in range(3)
        ]
        
        # 模拟 ClientSession 和响应
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="")
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = AsyncMock()
        mock_session.get = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        mock_client_session_class.return_value.__aenter__.return_value = mock_session
        
        # 创建 APIChecker
        checker = APIChecker(concurrency=10, timeout=5, retries=3, cache_ttl=3600, force_refresh=False)
        
        # 并发检查 APIConfig
        results = await checker.check_apis(api_configs)
        
        # 验证结果
        assert len(results) == 3
        for result in results:
            result_dict = asdict(result)
            assert result_dict["status_code"] == 200
            assert result_dict["error"] is None
            assert result_dict["status"] == "success"  # 验收标准字段


class TestAPICheckResult:
    """测试 APICheckResult 数据类"""
    
    def test_result_creation_success(self):
        """测试成功结果的创建"""
        result = APICheckResult(
            name="Test API",
            link="https://api.example.com",
            status_code=200,
            response_time=150.5,
            error=None,
            checked_at="2024-01-01T12:00:00",
            from_cache=False
        )
        
        assert result.name == "Test API"
        assert result.status_code == 200
        assert result.response_time == 150.5
        assert result.error is None
        assert result.http_status == 200  # 验收标准字段
        assert result.response_time_ms == 150.5  # 验收标准字段
        assert result.status == "success"  # 验收标准字段
    
    def test_result_creation_error(self):
        """测试错误结果的创建"""
        result = APICheckResult(
            name="Test API",
            link="https://api.example.com",
            status_code=500,
            response_time=100.0,
            error=None,
            checked_at="2024-01-01T12:00:00",
            from_cache=False
        )
        
        assert result.status_code == 500
        assert result.status == "error"  # 验收标准字段
    
    def test_result_creation_timeout(self):
        """测试超时结果的创建"""
        result = APICheckResult(
            name="Test API",
            link="https://api.example.com",
            status_code=None,
            response_time=None,
            error="Timeout error",
            checked_at="2024-01-01T12:00:00",
            from_cache=False
        )
        
        assert result.error == "Timeout error"
        assert result.status == "timeout"  # 验收标准字段
    
    def test_result_creation_connection_error(self):
        """测试连接错误结果的创建"""
        result = APICheckResult(
            name="Test API",
            link="https://api.example.com",
            status_code=None,
            response_time=None,
            error="Connection refused",
            checked_at="2024-01-01T12:00:00",
            from_cache=False
        )
        
        assert result.error == "Connection refused"
        assert result.status == "error"  # 验收标准字段
    
    def test_result_asdict(self):
        """测试 asdict 方法是否包含所有字段"""
        result = APICheckResult(
            name="Test API",
            link="https://api.example.com",
            status_code=200,
            response_time=150.5,
            error=None,
            checked_at="2024-01-01T12:00:00",
            from_cache=False
        )
        
        # 验证结果可序列化
        result_dict = asdict(result)
        assert isinstance(result_dict, dict)
        assert result_dict['name'] == "Test API"
        assert result_dict['link'] == "https://api.example.com"
        
        # 验证验收标准字段
        assert 'http_status' in result_dict
        assert 'response_time_ms' in result_dict
        assert 'status' in result_dict


if __name__ == "__main__":
    pytest.main(["-v", __file__])