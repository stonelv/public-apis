#!/usr/bin/env python3
"""
API 可用性检测工具

一个用于并发检测公共API可用性的CLI工具，支持JSON/CSV输入输出、缓存、重试策略等功能。
"""

import os
import sys
import json
import csv
import time
import hashlib
import argparse
import logging
from typing import List, Dict, Optional, Tuple, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('api_checker.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class APIConfig:
    """API配置数据类"""
    name: str
    link: str
    category: Optional[str] = None
    description: Optional[str] = None


@dataclass
class CheckResult:
    """检测结果数据类"""
    name: str
    link: str
    status_code: Optional[int]
    response_time_ms: Optional[float]
    error_message: Optional[str]
    check_time: str
    category: Optional[str] = None
    description: Optional[str] = None


class APIChecker:
    """API检测工具类"""
    
    def __init__(
        self,
        concurrency: int = 10,
        timeout: int = 10,
        retries: int = 3,
        backoff_factor: float = 0.5,
        cache_ttl: int = 3600,
        force_refresh: bool = False
    ):
        """
        初始化API检测器
        
        Args:
            concurrency: 并发请求数
            timeout: 超时时间(秒)
            retries: 重试次数
            backoff_factor: 退避因子
            cache_ttl: 缓存TTL(秒)
            force_refresh: 是否强制刷新缓存
        """
        self.concurrency = concurrency
        self.timeout = timeout
        self.retries = retries
        self.backoff_factor = backoff_factor
        self.cache_ttl = cache_ttl
        self.force_refresh = force_refresh
        
        # 创建带重试策略的会话
        self.session = self._create_session()
        
        # 缓存目录
        self.cache_dir = Path('cache')
        self.cache_dir.mkdir(exist_ok=True)
    
    def _create_session(self) -> requests.Session:
        """创建带重试策略的会话"""
        session = requests.Session()
        
        # 配置重试策略
        retry_strategy = Retry(
            total=self.retries,
            backoff_factor=self.backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        
        return session
    
    def _get_cache_key(self, url: str) -> str:
        """生成缓存键"""
        return hashlib.md5(url.encode('utf-8')).hexdigest()
    
    def _get_cache_path(self, url: str) -> Path:
        """获取缓存文件路径"""
        cache_key = self._get_cache_key(url)
        return self.cache_dir / f"{cache_key}.json"
    
    def _is_cache_valid(self, url: str) -> bool:
        """检查缓存是否有效"""
        if self.force_refresh:
            return False
            
        cache_path = self._get_cache_path(url)
        if not cache_path.exists():
            return False
            
        # 检查缓存是否过期
        file_mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - file_mtime > timedelta(seconds=self.cache_ttl):
            return False
            
        return True
    
    def _load_cache(self, url: str) -> Optional[CheckResult]:
        """从缓存加载结果"""
        cache_path = self._get_cache_path(url)
        if not cache_path.exists():
            return None
            
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return CheckResult(**data)
        except Exception as e:
            logger.warning(f"加载缓存失败 {url}: {e}")
            return None
    
    def _save_cache(self, result: CheckResult) -> None:
        """保存结果到缓存"""
        cache_path = self._get_cache_path(result.link)
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(asdict(result), f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"保存缓存失败 {result.link}: {e}")
    
    def _check_api(self, api: APIConfig) -> CheckResult:
        """检查单个API的可用性"""
        # 检查缓存
        if self._is_cache_valid(api.link):
            cached_result = self._load_cache(api.link)
            if cached_result:
                logger.debug(f"使用缓存结果: {api.link}")
                return cached_result
        
        check_time = datetime.now().isoformat()
        
        try:
            start_time = time.time()
            
            # 发送请求
            response = self.session.get(
                api.link,
                timeout=self.timeout,
                allow_redirects=True
            )
            
            response_time_ms = (time.time() - start_time) * 1000
            
            result = CheckResult(
                name=api.name,
                link=api.link,
                status_code=response.status_code,
                response_time_ms=round(response_time_ms, 2),
                error_message=None,
                check_time=check_time,
                category=api.category,
                description=api.description
            )
            
            # 保存缓存
            self._save_cache(result)
            
            logger.info(f"API {api.name} - 状态码: {response.status_code}, 响应时间: {response_time_ms:.2f}ms")
            
        except requests.exceptions.RequestException as e:
            response_time_ms = (time.time() - start_time) * 1000
            error_msg = str(e)
            
            result = CheckResult(
                name=api.name,
                link=api.link,
                status_code=None,
                response_time_ms=round(response_time_ms, 2),
                error_message=error_msg,
                check_time=check_time,
                category=api.category,
                description=api.description
            )
            
            # 保存缓存
            self._save_cache(result)
            
            logger.error(f"API {api.name} - 错误: {error_msg}")
        
        return result
    
    def load_apis_from_json(self, file_path: str) -> List[APIConfig]:
        """从JSON文件加载API列表"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            apis = []
            for item in data:
                apis.append(APIConfig(
                    name=item.get('name', 'Unknown'),
                    link=item.get('link', ''),
                    category=item.get('category'),
                    description=item.get('description')
                ))
            
            return apis
        except Exception as e:
            logger.error(f"加载JSON文件失败: {e}")
            raise
    
    def load_apis_from_csv(self, file_path: str) -> List[APIConfig]:
        """从CSV文件加载API列表"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
            apis = []
            for row in reader:
                apis.append(APIConfig(
                    name=row.get('name', 'Unknown'),
                    link=row.get('link', ''),
                    category=row.get('category'),
                    description=row.get('description')
                ))
            
            return apis
        except Exception as e:
            logger.error(f"加载CSV文件失败: {e}")
            raise
    
    def load_apis(self, file_path: str) -> List[APIConfig]:
        """根据文件扩展名加载API列表"""
        ext = Path(file_path).suffix.lower()
        
        if ext == '.json':
            return self.load_apis_from_json(file_path)
        elif ext == '.csv':
            return self.load_apis_from_csv(file_path)
        else:
            raise ValueError(f"不支持的文件格式: {ext}")
    
    def save_results_to_json(self, results: List[CheckResult], file_path: str) -> None:
        """保存结果到JSON文件"""
        try:
            data = [asdict(result) for result in results]
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"结果已保存到: {file_path}")
        except Exception as e:
            logger.error(f"保存JSON文件失败: {e}")
            raise
    
    def save_results_to_csv(self, results: List[CheckResult], file_path: str) -> None:
        """保存结果到CSV文件"""
        try:
            fieldnames = [
                'name', 'link', 'status_code', 'response_time_ms',
                'error_message', 'check_time', 'category', 'description'
            ]
            
            with open(file_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for result in results:
                    row = asdict(result)
                    # 处理None值
                    for key, value in row.items():
                        if value is None:
                            row[key] = ''
                    writer.writerow(row)
            
            logger.info(f"结果已保存到: {file_path}")
        except Exception as e:
            logger.error(f"保存CSV文件失败: {e}")
            raise
    
    def save_results(self, results: List[CheckResult], file_path: str) -> None:
        """根据文件扩展名保存结果"""
        ext = Path(file_path).suffix.lower()
        
        if ext == '.json':
            self.save_results_to_json(results, file_path)
        elif ext == '.csv':
            self.save_results_to_csv(results, file_path)
        else:
            raise ValueError(f"不支持的文件格式: {ext}")
    
    def run(self, input_file: str, output_file: str) -> List[CheckResult]:
        """运行API检测"""
        logger.info("开始API检测...")
        
        # 加载API列表
        apis = self.load_apis(input_file)
        logger.info(f"共加载 {len(apis)} 个API")
        
        # 并发检测
        results = []
        
        with ThreadPoolExecutor(max_workers=self.concurrency) as executor:
            # 提交所有任务
            future_to_api = {executor.submit(self._check_api, api): api for api in apis}
            
            # 处理结果
            for future in as_completed(future_to_api):
                api = future_to_api[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"处理API {api.name} 时出错: {e}")
        
        # 保存结果
        self.save_results(results, output_file)
        
        # 生成统计信息
        self._generate_stats(results)
        
        logger.info("API检测完成!")
        return results
    
    def _generate_stats(self, results: List[CheckResult]) -> None:
        """生成统计信息"""
        total = len(results)
        successful = sum(1 for r in results if r.status_code and 200 <= r.status_code < 300)
        failed = total - successful
        
        avg_response_time = sum(
            r.response_time_ms for r in results if r.response_time_ms is not None
        ) / total if total > 0 else 0
        
        logger.info("=" * 50)
        logger.info(f"检测统计:")
        logger.info(f"总API数: {total}")
        logger.info(f"成功: {successful} ({successful/total*100:.1f}%)")
        logger.info(f"失败: {failed} ({failed/total*100:.1f}%)")
        logger.info(f"平均响应时间: {avg_response_time:.2f}ms")
        logger.info("=" * 50)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='API可用性检测工具 - 并发检测公共API的可用性并生成报告'
    )
    
    parser.add_argument(
        '--input', '-i',
        required=True,
        help='输入文件路径 (JSON或CSV格式)'
    )
    
    parser.add_argument(
        '--output', '-o',
        required=True,
        help='输出文件路径 (JSON或CSV格式)'
    )
    
    parser.add_argument(
        '--concurrency', '-c',
        type=int,
        default=10,
        help='并发请求数 (默认: 10)'
    )
    
    parser.add_argument(
        '--timeout', '-t',
        type=int,
        default=10,
        help='超时时间(秒) (默认: 10)'
    )
    
    parser.add_argument(
        '--retries', '-r',
        type=int,
        default=3,
        help='重试次数 (默认: 3)'
    )
    
    parser.add_argument(
        '--backoff-factor',
        type=float,
        default=0.5,
        help='退避因子 (默认: 0.5)'
    )
    
    parser.add_argument(
        '--cache-ttl',
        type=int,
        default=3600,
        help='缓存TTL(秒) (默认: 3600)'
    )
    
    parser.add_argument(
        '--force', '-f',
        action='store_true',
        help='强制刷新缓存 (忽略缓存TTL)'
    )
    
    args = parser.parse_args()
    
    # 验证输入文件是否存在
    if not Path(args.input).exists():
        logger.error(f"输入文件不存在: {args.input}")
        sys.exit(1)
    
    # 创建输出目录
    output_dir = Path(args.output).parent
    output_dir.mkdir(exist_ok=True)
    
    try:
        # 创建检测器并运行
        checker = APIChecker(
            concurrency=args.concurrency,
            timeout=args.timeout,
            retries=args.retries,
            backoff_factor=args.backoff_factor,
            cache_ttl=args.cache_ttl,
            force_refresh=args.force
        )
        
        checker.run(args.input, args.output)
        
    except Exception as e:
        logger.error(f"运行失败: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
