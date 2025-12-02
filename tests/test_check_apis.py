#!/usr/bin/env python3
"""
APIs 检查工具的单元测试
"""

import pytest
import asyncio
import json
import csv
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

# 添加 scripts 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
import sys
import check_apis
from check_apis import (
    DataReader, ReportGenerator, CacheManager, APIChecker,
    APIConfig, APICheckResult
)

class TestDataReader:
    """数据读取器测试"""
    
    def test_read_json(self):
        """测试读取 JSON 文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump([
                {
                    "name": "Test API",
                    "link": "https://api.example.com",
                    "description": "Test Description",
                    "auth": "apiKey",
                    "https": True,
                    "cors": "yes"
                }
            ], f)
            temp_path = f.name
        
        try:
            apis = DataReader.read_json(temp_path)
            assert len(apis) == 1
            assert apis[0].name == "Test API"
            assert apis[0].link == "https://api.example.com"
            assert apis[0].description == "Test Description"
            assert apis[0].auth == "apiKey"
            assert apis[0].https == True
            assert apis[0].cors == "yes"
        finally:
            os.unlink(temp_path)
    
    def test_read_csv(self):
        """测试读取 CSV 文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write("name,link,description,auth,https,cors\n")
            f.write("Test API,https://api.example.com,Test Description,apiKey,True,yes\n")
            temp_path = f.name
        
        try:
            apis = DataReader.read_csv(temp_path)
            assert len(apis) == 1
            assert apis[0].name == "Test API"
            assert apis[0].link == "https://api.example.com"
            assert apis[0].description == "Test Description"
            assert apis[0].auth == "apiKey"
        finally:
            os.unlink(temp_path)
    
    def test_read_unsupported_format(self):
        """测试读取不支持的文件格式"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("test")
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError):
                DataReader.read(temp_path)
        finally:
            os.unlink(temp_path)

class TestReportGenerator:
    """报告生成器测试"""
    
    def test_generate_json(self):
        """测试生成 JSON 报告"""
        results = [
            APICheckResult(
                name="Test API",
                link="https://api.example.com",
                status_code=200,
                response_time=100.5,
                error=None,
                checked_at=datetime.now().isoformat()
            )
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            temp_path = f.name
        
        try:
            ReportGenerator.generate_json(results, temp_path)
            
            with open(temp_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            assert len(data) == 1
            assert data[0]['name'] == "Test API"
            assert data[0]['status_code'] == 200
            assert data[0]['response_time'] == 100.5
        finally:
            os.unlink(temp_path)
    
    def test_generate_csv(self):
        """测试生成 CSV 报告"""
        results = [
            APICheckResult(
                name="Test API",
                link="https://api.example.com",
                status_code=200,
                response_time=100.5,
                error=None,
                checked_at=datetime.now().isoformat()
            )
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            temp_path = f.name
        
        try:
            ReportGenerator.generate_csv(results, temp_path)
            
            with open(temp_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
            assert len(rows) == 1
            assert rows[0]['name'] == "Test API"
            assert rows[0]['status_code'] == "200"
            assert rows[0]['response_time'] == "100.5"
        finally:
            os.unlink(temp_path)
    
    def test_generate_unsupported_format(self):
        """测试生成不支持的格式"""
        results = []
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError):
                ReportGenerator.generate(results, temp_path)
        finally:
            os.unlink(temp_path)

class TestCacheManager:
    """缓存管理器测试"""
    
    def setup_method(self):
        """测试前准备"""
        self.cache_dir = tempfile.mkdtemp()
        self.cache_manager = CacheManager(cache_ttl=3600, cache_dir=self.cache_dir)
    
    def teardown_method(self):
        """测试后清理"""
        # 清理临时目录
        import shutil
        shutil.rmtree(self.cache_dir)
    
    def test_get_set_cache(self):
        """测试缓存的读写"""
        url = "https://api.example.com"
        data = {"status_code": 200, "response_time": 100.5}
        
        # 设置缓存
        self.cache_manager.set(url, data)
        
        # 获取缓存
        cached_data = self.cache_manager.get(url)
        
        assert cached_data is not None
        assert cached_data['status_code'] == 200
        assert cached_data['response_time'] == 100.5
    
    def test_cache_expiration(self):
        """测试缓存过期"""
        url = "https://api.example.com"
        data = {"status_code": 200}
        
        # 创建过期的缓存
        cache_manager = CacheManager(cache_ttl=1, cache_dir=self.cache_dir)  # TTL 1秒
        cache_manager.set(url, data)
        
        # 等待缓存过期
        import time
        time.sleep(2)
        
        # 应该返回 None
        assert cache_manager.get(url) is None
    
    def test_clear_all(self):
        """测试清除所有缓存"""
        # 设置多个缓存
        self.cache_manager.set("https://api.example.com", {"status": 200})
        self.cache_manager.set("https://api.example2.com", {"status": 200})
        
        # 清除所有缓存
        self.cache_manager.clear_all()
        
        # 验证缓存已清除
        assert len(list(Path(self.cache_dir).glob("*.json"))) == 0

class TestAPIChecker:
    """API 检查器测试"""
    
    @pytest.mark.asyncio
    async def test_check_single_api_success(self, mocker):
        """测试成功检查单个 API"""
        # Mock aiohttp.ClientSession
        mock_response = mocker.Mock()
        mock_response.status = 200
        mock_response.headers.return_value = {}
        
        mock_get = mocker.AsyncMock(return_value=mock_response)
        mock_session = mocker.Mock()
        mock_session.get = mock_get
        
        # Mock asyncio.Queue
        mock_queue = mocker.Mock()
        mock_queue.put = mocker.AsyncMock()
        
        checker = APIChecker(concurrency=1, timeout=5, retries=0)
        api = APIConfig(name="Test API", link="https://api.example.com")
        
        result = await checker._check_single_api(mock_session, api, mock_queue)
        
        assert result.status_code == 200
        assert result.error is None
        assert result.response_time is not None
        mock_get.assert_called_once_with("https://api.example.com", timeout=mocker.ANY)
    
    @pytest.mark.asyncio
    async def test_check_single_api_failure(self, mocker):
        """测试检查单个 API 失败"""
        # Mock 请求失败
        mock_get = mocker.AsyncMock(side_effect=Exception("Connection error"))
        mock_session = mocker.Mock()
        mock_session.get = mock_get
        
        mock_queue = mocker.Mock()
        mock_queue.put = mocker.AsyncMock()
        
        checker = APIChecker(concurrency=1, timeout=5, retries=0)
        api = APIConfig(name="Test API", link="https://api.example.com")
        
        result = await checker._check_single_api(mock_session, api, mock_queue)
        
        assert result.status_code is None
        assert result.error == "Connection error"
    
    @pytest.mark.asyncio
    async def test_check_single_api_retry(self, mocker):
        """测试重试机制"""
        # 第一次失败，第二次成功
        mock_response1 = mocker.Mock()
        mock_response1.status = 500
        
        mock_response2 = mocker.Mock()
        mock_response2.status = 200
        
        mock_get = mocker.AsyncMock(side_effect=[
            Exception("Server error"),
            mock_response2
        ])
        mock_session = mocker.Mock()
        mock_session.get = mock_get
        
        mock_queue = mocker.Mock()
        mock_queue.put = mocker.AsyncMock()
        
        # Mock asyncio.sleep 避免实际等待
        mocker.patch('asyncio.sleep', return_value=None)
        
        checker = APIChecker(concurrency=1, timeout=5, retries=1)
        api = APIConfig(name="Test API", link="https://api.example.com")
        
        result = await checker._check_single_api(mock_session, api, mock_queue)
        
        # 应该重试了两次（初始请求 + 1次重试）
        assert mock_get.call_count == 2
        assert result.status_code == 200
    
    @pytest.mark.asyncio
    async def test_check_apis_concurrent(self, mocker):
        """测试并发检查多个 API"""
        # Mock aiohttp.ClientSession
        mock_response = mocker.Mock()
        mock_response.status = 200
        mock_response.headers.return_value = {}
        
        mock_get = mocker.AsyncMock(return_value=mock_response)
        
        # Mock ClientSession 上下文管理器
        mock_session = mocker.Mock()
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        mock_session.get = mock_get
        
        mocker.patch('aiohttp.ClientSession', return_value=mock_session)
        mocker.patch('aiohttp.TCPConnector')
        
        # 模拟多个 API
        apis = [
            APIConfig(name=f"API {i}", link=f"https://api.example{i}.com")
            for i in range(5)
        ]
        
        checker = APIChecker(concurrency=2)
        results = await checker.check_apis(apis)
        
        assert len(results) == 5
        assert all(result.status_code == 200 for result in results)
        assert mock_get.call_count == 5

if __name__ == "__main__":
    pytest.main([__file__])