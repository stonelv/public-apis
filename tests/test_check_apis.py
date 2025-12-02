#!/usr/bin/env python3
"""
API检测工具单元测试
"""

import os
import sys
import json
import csv
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from pathlib import Path

import pytest
import requests
from requests.exceptions import RequestException, Timeout, ConnectionError

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.check_apis import APIChecker, APIConfig, CheckResult


class TestAPIChecker:
    """API检测器单元测试"""
    
    def test_init_defaults(self):
        """测试默认初始化参数"""
        checker = APIChecker()
        
        assert checker.concurrency == 10
        assert checker.timeout == 10
        assert checker.retries == 3
        assert checker.backoff_factor == 0.5
        assert checker.cache_ttl == 3600
        assert checker.force_refresh is False
    
    def test_init_custom_params(self):
        """测试自定义初始化参数"""
        checker = APIChecker(
            concurrency=20,
            timeout=15,
            retries=5,
            backoff_factor=1.0,
            cache_ttl=7200,
            force_refresh=True
        )
        
        assert checker.concurrency == 20
        assert checker.timeout == 15
        assert checker.retries == 5
        assert checker.backoff_factor == 1.0
        assert checker.cache_ttl == 7200
        assert checker.force_refresh is True
    
    def test_create_session(self):
        """测试创建会话"""
        checker = APIChecker()
        assert checker.session is not None
    
    def test_get_cache_key(self):
        """测试生成缓存键"""
        checker = APIChecker()
        url = "https://example.com/api"
        
        key1 = checker._get_cache_key(url)
        key2 = checker._get_cache_key(url)
        
        # 相同URL应该生成相同的键
        assert key1 == key2
        # 键应该是MD5哈希值
        assert len(key1) == 32
    
    def test_get_cache_path(self):
        """测试获取缓存路径"""
        checker = APIChecker()
        url = "https://example.com/api"
        
        path = checker._get_cache_path(url)
        assert isinstance(path, Path)
        assert path.parent == checker.cache_dir
        assert path.suffix == '.json'
    
    @patch('scripts.check_apis.datetime')
    @patch('scripts.check_apis.Path.exists')
    @patch('scripts.check_apis.Path.stat')
    @patch('scripts.check_apis.Path.is_dir')
    def test_is_cache_valid(self, mock_is_dir, mock_stat, mock_exists, mock_datetime):
        """测试缓存有效性检查"""
        # 模拟缓存目录存在
        mock_is_dir.return_value = True
        
        checker = APIChecker(cache_ttl=3600)
        url = "https://example.com/api"
        
        # 测试缓存不存在
        mock_exists.return_value = False
        assert checker._is_cache_valid(url) is False
        
        # 测试缓存存在且未过期
        mock_exists.return_value = True
        mock_datetime.fromtimestamp.return_value = datetime(2023, 1, 1, 11, 0, 0)
        mock_datetime.now.return_value = datetime(2023, 1, 1, 12, 0, 0)
        mock_stat.return_value.st_mtime = 1672531200  # 2023-01-01 11:00:00
        
        assert checker._is_cache_valid(url) is True
        
        # 测试缓存过期
        mock_datetime.fromtimestamp.return_value = datetime(2023, 1, 1, 10, 0, 0)
        
        # 修改缓存TTL为30分钟
        checker.cache_ttl = 1800
        assert checker._is_cache_valid(url) is False
        
        # 测试强制刷新
        checker.force_refresh = True
        assert checker._is_cache_valid(url) is False
    
    @patch('scripts.check_apis.open')
    @patch('scripts.check_apis.json.load')
    def test_load_cache(self, mock_json_load, mock_open):
        """测试从缓存加载"""
        checker = APIChecker()
        url = "https://example.com/api"
        
        # 测试缓存文件不存在
        with patch('scripts.check_apis.Path.exists', return_value=False):
            assert checker._load_cache(url) is None
        
        # 测试缓存文件存在且有效
        with patch('scripts.check_apis.Path.exists', return_value=True):
            mock_json_load.return_value = {
                'name': 'Test API',
                'link': url,
                'status_code': 200,
                'response_time_ms': 100.5,
                'error_message': None,
                'check_time': '2023-01-01T12:00:00'
            }
            
            result = checker._load_cache(url)
            assert result is not None
            assert result.name == 'Test API'
            assert result.status_code == 200
    
    @patch('scripts.check_apis.open')
    @patch('scripts.check_apis.json.dump')
    def test_save_cache(self, mock_json_dump, mock_open):
        """测试保存缓存"""
        checker = APIChecker()
        
        result = CheckResult(
            name='Test API',
            link='https://example.com/api',
            status_code=200,
            response_time_ms=100.5,
            error_message=None,
            check_time='2023-01-01T12:00:00'
        )
        
        checker._save_cache(result)
        mock_open.assert_called_once()
        mock_json_dump.assert_called_once()
    
    @patch('scripts.check_apis.APIChecker._is_cache_valid')
    @patch('scripts.check_apis.APIChecker._load_cache')
    @patch('scripts.check_apis.APIChecker._save_cache')
    @patch('scripts.check_apis.requests.Session.get')
    def test_check_api_success(self, mock_get, mock_save_cache, mock_load_cache, mock_is_cache_valid):
        """测试成功检查API"""
        checker = APIChecker()
        api = APIConfig(name='Test API', link='https://example.com/api')
        
        # 模拟缓存无效
        mock_is_cache_valid.return_value = False
        
        # 模拟成功响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        result = checker._check_api(api)
        
        assert result.name == 'Test API'
        assert result.status_code == 200
        assert result.error_message is None
        assert result.response_time_ms is not None
        
        mock_get.assert_called_once()
        mock_save_cache.assert_called_once()
    
    @patch('scripts.check_apis.APIChecker._is_cache_valid')
    @patch('scripts.check_apis.APIChecker._load_cache')
    @patch('scripts.check_apis.APIChecker._save_cache')
    @patch('scripts.check_apis.requests.Session.get')
    def test_check_api_failure(self, mock_get, mock_save_cache, mock_load_cache, mock_is_cache_valid):
        """测试API检查失败"""
        checker = APIChecker()
        api = APIConfig(name='Test API', link='https://example.com/api')
        
        # 模拟缓存无效
        mock_is_cache_valid.return_value = False
        
        # 模拟请求超时
        mock_get.side_effect = Timeout("Connection timed out")
        
        result = checker._check_api(api)
        
        assert result.name == 'Test API'
        assert result.status_code is None
        assert 'timed out' in result.error_message
        assert result.response_time_ms is not None
        
        mock_get.assert_called_once()
        # 失败的请求也应该保存缓存
        mock_save_cache.assert_called_once()
    
    @patch('scripts.check_apis.APIChecker._is_cache_valid')
    @patch('scripts.check_apis.APIChecker._load_cache')
    def test_check_api_cached(self, mock_load_cache, mock_is_cache_valid):
        """测试使用缓存结果"""
        checker = APIChecker()
        api = APIConfig(name='Test API', link='https://example.com/api')
        
        # 模拟缓存有效
        mock_is_cache_valid.return_value = True
        
        # 模拟缓存结果
        cached_result = CheckResult(
            name='Test API',
            link='https://example.com/api',
            status_code=200,
            response_time_ms=100.5,
            error_message=None,
            check_time='2023-01-01T12:00:00'
        )
        mock_load_cache.return_value = cached_result
        
        result = checker._check_api(api)
        
        assert result == cached_result
        mock_load_cache.assert_called_once()
    
    @patch('scripts.check_apis.open')
    @patch('scripts.check_apis.json.load')
    def test_load_apis_from_json(self, mock_json_load, mock_open):
        """测试从JSON加载API"""
        checker = APIChecker()
        
        # 模拟JSON数据
        mock_json_load.return_value = [
            {
                'name': 'API 1',
                'link': 'https://example.com/api1',
                'category': 'Test',
                'description': 'Test API 1'
            },
            {
                'name': 'API 2',
                'link': 'https://example.com/api2'
            }
        ]
        
        apis = checker.load_apis_from_json('test.json')
        
        assert len(apis) == 2
        assert apis[0].name == 'API 1'
        assert apis[0].link == 'https://example.com/api1'
        assert apis[1].name == 'API 2'
        assert apis[1].link == 'https://example.com/api2'
    
    @patch('scripts.check_apis.open')
    @patch('scripts.check_apis.csv.DictReader')
    def test_load_apis_from_csv(self, mock_dict_reader, mock_open):
        """测试从CSV加载API"""
        checker = APIChecker()
        
        # 模拟CSV数据
        mock_dict_reader.return_value = [
            {
                'name': 'API 1',
                'link': 'https://example.com/api1',
                'category': 'Test',
                'description': 'Test API 1'
            },
            {
                'name': 'API 2',
                'link': 'https://example.com/api2'
            }
        ]
        
        apis = checker.load_apis_from_csv('test.csv')
        
        assert len(apis) == 2
        assert apis[0].name == 'API 1'
        assert apis[0].link == 'https://example.com/api1'
    
    @patch('scripts.check_apis.APIChecker.load_apis_from_json')
    def test_load_apis_json(self, mock_load_json):
        """测试加载JSON格式API"""
        checker = APIChecker()
        
        mock_load_json.return_value = [APIConfig(name='Test', link='https://example.com')]
        
        apis = checker.load_apis('test.json')
        
        assert len(apis) == 1
        mock_load_json.assert_called_once()
    
    @patch('scripts.check_apis.APIChecker.load_apis_from_csv')
    def test_load_apis_csv(self, mock_load_csv):
        """测试加载CSV格式API"""
        checker = APIChecker()
        
        mock_load_csv.return_value = [APIConfig(name='Test', link='https://example.com')]
        
        apis = checker.load_apis('test.csv')
        
        assert len(apis) == 1
        mock_load_csv.assert_called_once()
    
    def test_load_apis_invalid_format(self):
        """测试加载不支持的文件格式"""
        checker = APIChecker()
        
        with pytest.raises(ValueError):
            checker.load_apis('test.txt')
    
    @patch('scripts.check_apis.open')
    @patch('scripts.check_apis.json.dump')
    def test_save_results_to_json(self, mock_json_dump, mock_open):
        """测试保存结果到JSON"""
        checker = APIChecker()
        
        results = [
            CheckResult(
                name='Test API',
                link='https://example.com/api',
                status_code=200,
                response_time_ms=100.5,
                error_message=None,
                check_time='2023-01-01T12:00:00'
            )
        ]
        
        checker.save_results_to_json(results, 'output.json')
        
        mock_open.assert_called_once()
        mock_json_dump.assert_called_once()
    
    @patch('scripts.check_apis.open')
    @patch('scripts.check_apis.csv.DictWriter')
    def test_save_results_to_csv(self, mock_dict_writer, mock_open):
        """测试保存结果到CSV"""
        checker = APIChecker()
        
        results = [
            CheckResult(
                name='Test API',
                link='https://example.com/api',
                status_code=200,
                response_time_ms=100.5,
                error_message=None,
                check_time='2023-01-01T12:00:00'
            )
        ]
        
        checker.save_results_to_csv(results, 'output.csv')
        
        mock_open.assert_called_once()
        mock_dict_writer.return_value.writeheader.assert_called_once()
        mock_dict_writer.return_value.writerow.assert_called_once()
    
    @patch('scripts.check_apis.APIChecker.save_results_to_json')
    def test_save_results_json(self, mock_save_json):
        """测试保存JSON格式结果"""
        checker = APIChecker()
        results = []
        
        checker.save_results(results, 'output.json')
        mock_save_json.assert_called_once()
    
    @patch('scripts.check_apis.APIChecker.save_results_to_csv')
    def test_save_results_csv(self, mock_save_csv):
        """测试保存CSV格式结果"""
        checker = APIChecker()
        results = []
        
        checker.save_results(results, 'output.csv')
        mock_save_csv.assert_called_once()
    
    def test_save_results_invalid_format(self):
        """测试保存不支持的文件格式"""
        checker = APIChecker()
        
        with pytest.raises(ValueError):
            checker.save_results([], 'output.txt')
    
    @patch('scripts.check_apis.APIChecker.load_apis')
    @patch('scripts.check_apis.APIChecker._check_api')
    @patch('scripts.check_apis.APIChecker.save_results')
    @patch('scripts.check_apis.APIChecker._generate_stats')
    def test_run(self, mock_generate_stats, mock_save_results, mock_check_api, mock_load_apis):
        """测试运行API检测"""
        checker = APIChecker()
        
        # 模拟API列表
        mock_apis = [
            APIConfig(name='API 1', link='https://example.com/api1'),
            APIConfig(name='API 2', link='https://example.com/api2')
        ]
        mock_load_apis.return_value = mock_apis
        
        # 模拟检测结果
        mock_results = [
            CheckResult(
                name='API 1',
                link='https://example.com/api1',
                status_code=200,
                response_time_ms=100.5,
                error_message=None,
                check_time='2023-01-01T12:00:00'
            )
        ]
        mock_check_api.return_value = mock_results[0]
        
        results = checker.run('input.json', 'output.json')
        
        assert len(results) == 2  # 应该返回2个结果
        mock_load_apis.assert_called_once()
        assert mock_check_api.call_count == 2
        mock_save_results.assert_called_once()
        mock_generate_stats.assert_called_once()
    
    @patch('scripts.check_apis.logger.info')
    def test_generate_stats(self, mock_logger_info):
        """测试生成统计信息"""
        checker = APIChecker()
        
        results = [
            CheckResult(
                name='API 1',
                link='https://example.com/api1',
                status_code=200,
                response_time_ms=100.5,
                error_message=None,
                check_time='2023-01-01T12:00:00'
            ),
            CheckResult(
                name='API 2',
                link='https://example.com/api2',
                status_code=404,
                response_time_ms=50.2,
                error_message='Not Found',
                check_time='2023-01-01T12:00:01'
            ),
            CheckResult(
                name='API 3',
                link='https://example.com/api3',
                status_code=None,
                response_time_ms=200.0,
                error_message='Connection Error',
                check_time='2023-01-01T12:00:02'
            )
        ]
        
        checker._generate_stats(results)
        
        # 验证统计信息是否正确生成
        calls = [str(call) for call in mock_logger_info.call_args_list]
        assert any('总API数: 3' in call for call in calls)
        assert any('成功: 1' in call for call in calls)
        assert any('失败: 2' in call for call in calls)
        assert any('平均响应时间' in call for call in calls)


def test_api_config_dataclass():
    """测试APIConfig数据类"""
    config = APIConfig(
        name='Test API',
        link='https://example.com/api',
        category='Test',
        description='Test description'
    )
    
    assert config.name == 'Test API'
    assert config.link == 'https://example.com/api'
    assert config.category == 'Test'
    assert config.description == 'Test description'


def test_check_result_dataclass():
    """测试CheckResult数据类"""
    result = CheckResult(
        name='Test API',
        link='https://example.com/api',
        status_code=200,
        response_time_ms=100.5,
        error_message=None,
        check_time='2023-01-01T12:00:00'
    )
    
    assert result.name == 'Test API'
    assert result.status_code == 200
    assert result.response_time_ms == 100.5
    assert result.error_message is None


if __name__ == '__main__':
    pytest.main([__file__])
