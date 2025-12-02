#!/usr/bin/env python3
"""
Public APIs 可用性检测工具

一个并发检测 public APIs 可用性的 Python CLI 工具，支持生成 JSON/CSV 报告
"""

import argparse
import asyncio
import aiohttp
import json
import csv
import time
import logging
import os
import hashlib
from typing import List, Dict, Optional, Union, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path

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
class APICheckResult:
    """API 检查结果数据类"""
    name: str
    link: str
    status_code: Optional[int]
    response_time: Optional[float]  # 毫秒
    error: Optional[str]
    checked_at: str  # ISO 格式时间
    from_cache: bool = False

@dataclass
class APIConfig:
    """API 配置数据类"""
    name: str
    link: str
    # 其他可能的字段（根据实际数据文件调整）
    description: Optional[str] = None
    auth: Optional[str] = None
    https: Optional[bool] = None
    cors: Optional[str] = None

class CacheManager:
    """本地缓存管理器"""
    
    def __init__(self, cache_ttl: int, cache_dir: str = ".cache"):
        self.cache_ttl = timedelta(seconds=cache_ttl)
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
    
    def _get_cache_key(self, url: str) -> str:
        """生成 URL 的缓存键"""
        return hashlib.md5(url.encode('utf-8')).hexdigest() + ".json"
    
    def get(self, url: str) -> Optional[Dict[str, Any]]:
        """从缓存获取数据"""
        cache_file = self.cache_dir / self._get_cache_key(url)
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)
                
            # 检查缓存是否过期
            cached_at = datetime.fromisoformat(data['cached_at'])
            if datetime.now() - cached_at > self.cache_ttl:
                logger.debug(f"缓存过期: {url}")
                os.remove(cache_file)
                return None
            
            return data['result']
        except Exception as e:
            logger.warning(f"读取缓存失败: {e}")
            return None
    
    def set(self, url: str, result: Dict[str, Any]):
        """保存数据到缓存"""
        try:
            cache_file = self.cache_dir / self._get_cache_key(url)
            data = {
                'cached_at': datetime.now().isoformat(),
                'result': result
            }
            
            with open(cache_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning(f"写入缓存失败: {e}")
    
    def clear_all(self):
        """清除所有缓存"""
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
            logger.info("缓存已清除")
        except Exception as e:
            logger.warning(f"清除缓存失败: {e}")

class DataReader:
    """数据读取器"""
    
    @staticmethod
    def read_json(file_path: str) -> List[APIConfig]:
        """从 JSON 文件读取 API 列表"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            apis = []
            for item in data:
                if isinstance(item, dict) and 'name' in item and 'link' in item:
                    apis.append(APIConfig(
                        name=item['name'],
                        link=item['link'],
                        description=item.get('description'),
                        auth=item.get('auth'),
                        https=item.get('https'),
                        cors=item.get('cors')
                    ))
            
            logger.info(f"从 JSON 文件读取 {len(apis)} 个 API")
            return apis
        except Exception as e:
            logger.error(f"读取 JSON 文件失败: {e}")
            raise
    
    @staticmethod
    def read_csv(file_path: str) -> List[APIConfig]:
        """从 CSV 文件读取 API 列表"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                apis = []
                for row in reader:
                    if 'name' in row and 'link' in row:
                        apis.append(APIConfig(
                            name=row['name'],
                            link=row['link'],
                            description=row.get('description'),
                            auth=row.get('auth'),
                            https=row.get('https'),
                            cors=row.get('cors')
                        ))
            
            logger.info(f"从 CSV 文件读取 {len(apis)} 个 API")
            return apis
        except Exception as e:
            logger.error(f"读取 CSV 文件失败: {e}")
            raise
    
    @staticmethod
    def read(file_path: str) -> List[APIConfig]:
        """自动识别文件格式并读取"""
        if file_path.lower().endswith('.json'):
            return DataReader.read_json(file_path)
        elif file_path.lower().endswith('.csv'):
            return DataReader.read_csv(file_path)
        else:
            raise ValueError("不支持的文件格式，只支持 JSON 和 CSV")

class ReportGenerator:
    """报告生成器"""
    
    @staticmethod
    def generate_json(results: List[APICheckResult], output_path: str):
        """生成 JSON 报告"""
        try:
            data = [asdict(result) for result in results]
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"JSON 报告已生成: {output_path}")
        except Exception as e:
            logger.error(f"生成 JSON 报告失败: {e}")
            raise
    
    @staticmethod
    def generate_csv(results: List[APICheckResult], output_path: str):
        """生成 CSV 报告"""
        try:
            if not results:
                logger.warning("没有结果数据可生成报告")
                return
            
            fieldnames = [field for field in dir(results[0]) 
                         if not field.startswith('_') and field != 'asdict']
            
            with open(output_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for result in results:
                    writer.writerow(asdict(result))
            
            logger.info(f"CSV 报告已生成: {output_path}")
        except Exception as e:
            logger.error(f"生成 CSV 报告失败: {e}")
            raise
    
    @staticmethod
    def generate(results: List[APICheckResult], output_path: str):
        """自动识别输出格式并生成报告"""
        if output_path.lower().endswith('.json'):
            ReportGenerator.generate_json(results, output_path)
        elif output_path.lower().endswith('.csv'):
            ReportGenerator.generate_csv(results, output_path)
        else:
            raise ValueError("不支持的输出格式，只支持 JSON 和 CSV")

class APIChecker:
    """API 检查器"""
    
    def __init__(
        self,
        concurrency: int = 10,
        timeout: int = 10,
        retries: int = 3,
        cache_ttl: int = 3600,
        force_refresh: bool = False
    ):
        self.concurrency = concurrency
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.retries = retries
        self.force_refresh = force_refresh
        self.cache_manager = CacheManager(cache_ttl)
        
        if force_refresh:
            self.cache_manager.clear_all()
    
    async def _check_single_api(
        self,
        session: aiohttp.ClientSession,
        api: APIConfig,
        progress: asyncio.Queue
    ) -> APICheckResult:
        """检查单个 API 的可用性"""
        try:
            # 尝试从缓存获取
            cached_result = self.cache_manager.get(api.link)
            if cached_result and not self.force_refresh:
                result = APICheckResult(**cached_result, from_cache=True)
                logger.debug(f"从缓存获取结果: {api.name}")
                await progress.put(1)
                return result
            
            start_time = time.time()
            status_code = None
            error = None
            
            # 带重试机制的请求
            for retry in range(self.retries + 1):
                try:
                    async with session.get(api.link, timeout=self.timeout) as response:
                        status_code = response.status
                        # 简单读取响应头以确保连接成功
                        await response.headers()
                        break
                except Exception as e:
                    error = str(e)
                    if retry < self.retries:
                        # 指数退避
                        await asyncio.sleep(2 ** retry)
                        logger.debug(f"重试 {retry + 1}/{self.retries} 失败: {api.name} - {e}")
                    else:
                        logger.error(f"检查 API 失败: {api.name} - {e}")
            
            response_time = (time.time() - start_time) * 1000  # 转换为毫秒
            
            result = APICheckResult(
                name=api.name,
                link=api.link,
                status_code=status_code,
                response_time=round(response_time, 2),
                error=error,
                checked_at=datetime.now().isoformat()
            )
            
            # 保存到缓存（仅当成功获取状态码时）
            if status_code is not None:
                self.cache_manager.set(api.link, asdict(result))
            
            await progress.put(1)
            return result
        
        except Exception as e:
            logger.error(f"检查 API 异常: {api.name} - {e}")
            result = APICheckResult(
                name=api.name,
                link=api.link,
                status_code=None,
                response_time=None,
                error=str(e),
                checked_at=datetime.now().isoformat()
            )
            await progress.put(1)
            return result
    
    async def _display_progress(self, total: int, progress: asyncio.Queue):
        """显示进度条"""
        processed = 0
        while processed < total:
            await progress.get()
            processed += 1
            percentage = (processed / total) * 100
            bar_length = 50
            filled_length = int(bar_length * processed // total)
            bar = '█' * filled_length + '-' * (bar_length - filled_length)
            print(f'\r进度: |{bar}| {percentage:.1f}% ({processed}/{total})', end='', flush=True)
        print()  # 换行
    
    async def check_apis(self, apis: List[APIConfig]) -> List[APICheckResult]:
        """批量检查 APIs"""
        if not apis:
            logger.warning("没有 API 需要检查")
            return []
        
        logger.info(f"开始检查 {len(apis)} 个 API...")
        logger.info(f"并发数: {self.concurrency}")
        logger.info(f"超时: {self.timeout.total}秒")
        logger.info(f"重试次数: {self.retries}")
        
        # 创建进度队列
        progress_queue = asyncio.Queue(maxsize=self.concurrency)
        
        # 创建进度显示任务
        progress_task = asyncio.create_task(
            self._display_progress(len(apis), progress_queue)
        )
        
        # 创建 HTTP 客户端会话
        connector = aiohttp.TCPConnector(limit=self.concurrency)
        
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = []
            for api in apis:
                task = self._check_single_api(session, api, progress_queue)
                tasks.append(task)
            
            # 并发执行所有任务
            results = await asyncio.gather(*tasks)
        
        # 等待进度任务完成
        await progress_task
        
        # 统计结果
        successful = sum(1 for r in results if r.status_code is not None and 200 <= r.status_code < 300)
        failed = sum(1 for r in results if r.status_code is None or r.status_code >= 400)
        cached = sum(1 for r in results if r.from_cache)
        
        logger.info(f"检查完成！")
        logger.info(f"成功: {successful}, 失败: {failed}, 缓存: {cached}")
        
        return results

def parse_args() -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='并发检测 public APIs 可用性并生成报告'
    )
    
    parser.add_argument(
        '--input', '-i',
        required=True,
        help='输入文件路径（支持 JSON/CSV）'
    )
    
    parser.add_argument(
        '--output', '-o',
        required=True,
        help='输出文件路径（支持 JSON/CSV）'
    )
    
    parser.add_argument(
        '--concurrency', '-c',
        type=int,
        default=10,
        help='并发请求数（默认: 10）'
    )
    
    parser.add_argument(
        '--timeout', '-t',
        type=int,
        default=10,
        help='超时时间（秒，默认: 10）'
    )
    
    parser.add_argument(
        '--retries', '-r',
        type=int,
        default=3,
        help='重试次数（默认: 3）'
    )
    
    parser.add_argument(
        '--cache-ttl',
        type=int,
        default=3600,
        help='缓存过期时间（秒，默认: 3600）'
    )
    
    parser.add_argument(
        '--force', '-f',
        action='store_true',
        help='强制刷新缓存（不使用现有缓存）'
    )
    
    return parser.parse_args()

def main():
    """主函数"""
    try:
        args = parse_args()
        
        # 验证参数
        if not os.path.exists(args.input):
            logger.error(f"输入文件不存在: {args.input}")
            exit(1)
        
        # 创建输出目录
        output_dir = os.path.dirname(args.output)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # 读取 API 列表
        logger.info(f"读取输入文件: {args.input}")
        apis = DataReader.read(args.input)
        
        # 检查 APIs
        checker = APIChecker(
            concurrency=args.concurrency,
            timeout=args.timeout,
            retries=args.retries,
            cache_ttl=args.cache_ttl,
            force_refresh=args.force
        )
        
        results = asyncio.run(checker.check_apis(apis))
        
        # 生成报告
        logger.info(f"生成报告: {args.output}")
        ReportGenerator.generate(results, args.output)
        
        logger.info("任务完成！")
        
    except KeyboardInterrupt:
        logger.info("用户中断程序")
    except Exception as e:
        logger.error(f"程序执行失败: {e}")
        exit(1)

if __name__ == "__main__":
    main()