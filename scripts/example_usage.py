#!/usr/bin/env python3
"""
API检测工具使用示例
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.check_apis import APIChecker


def example_basic():
    """基本用法示例"""
    print("=== 基本用法示例 ===")
    
    checker = APIChecker()
    results = checker.run(
        input_file='data/sample_apis.json',
        output_file='results/basic_results.json'
    )
    
    print(f"检测完成，共检测 {len(results)} 个API")
    print()


def example_custom_params():
    """自定义参数示例"""
    print("=== 自定义参数示例 ===")
    
    checker = APIChecker(
        concurrency=15,
        timeout=15,
        retries=5,
        backoff_factor=1.0,
        cache_ttl=7200  # 2小时缓存
    )
    
    results = checker.run(
        input_file='data/sample_apis.csv',
        output_file='results/custom_params_results.csv'
    )
    
    print(f"检测完成，共检测 {len(results)} 个API")
    print()


def example_force_refresh():
    """强制刷新缓存示例"""
    print("=== 强制刷新缓存示例 ===")
    
    checker = APIChecker(
        force_refresh=True
    )
    
    results = checker.run(
        input_file='data/sample_apis.json',
        output_file='results/force_refresh_results.json'
    )
    
    print(f"检测完成，共检测 {len(results)} 个API")
    print()


def example_csv_output():
    """CSV输出示例"""
    print("=== CSV输出示例 ===")
    
    checker = APIChecker()
    results = checker.run(
        input_file='data/sample_apis.json',
        output_file='results/csv_output.csv'
    )
    
    print(f"检测完成，共检测 {len(results)} 个API")
    print()


def main():
    """主函数"""
    # 创建结果目录
    Path('results').mkdir(exist_ok=True)
    
    # 运行所有示例
    example_basic()
    example_force_refresh()
    example_csv_output()
    
    print("所有示例运行完成！")
    print("结果文件已保存到 results/ 目录")


if __name__ == '__main__':
    main()
