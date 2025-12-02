# Public APIs 可用性检测工具

一个并发检测 public APIs 可用性的 Python CLI 工具，支持生成 JSON/CSV 报告。

## 功能特性

- 🚀 **并发检测**：支持可配置的并发请求数，提高检测效率
- 📊 **多格式支持**：支持从 JSON/CSV 文件读取 API 列表，生成 JSON/CSV 格式报告
- 🔄 **智能缓存**：带 TTL 的本地缓存机制，可配置缓存过期时间，支持强制刷新
- ⏱️ **超时与重试**：可配置超时时间和重试次数，带指数退避策略
- 📈 **实时进度**：显示检测进度条，实时了解检测状态
- 📝 **详细日志**：记录检测过程和结果到日志文件
- 🧪 **单元测试**：完整的 pytest 单元测试套件，mock 网络请求

## 技术栈

- Python 3.7+
- asyncio + aiohttp：异步 HTTP 请求
- dataclasses：数据结构定义
- argparse：命令行参数解析
- pytest：单元测试框架

## 安装依赖

```bash
pip install -r requirements.txt
```

### 依赖列表

- aiohttp >= 3.8.0
- pytest >= 7.0.0
- pytest-asyncio >= 0.21.0

## 命令行参数

| 参数 | 简写 | 类型 | 默认值 | 描述 |
|------|------|------|--------|------|
| `--input` | `-i` | 字符串 | 必填 | 输入文件路径（支持 JSON/CSV） |
| `--output` | `-o` | 字符串 | 必填 | 输出文件路径（支持 JSON/CSV） |
| `--concurrency` | `-c` | 整数 | 10 | 并发请求数 |
| `--timeout` | `-t` | 整数 | 10 | 超时时间（秒） |
| `--retries` | `-r` | 整数 | 3 | 重试次数 |
| `--cache-ttl` | - | 整数 | 3600 | 缓存过期时间（秒） |
| `--force` | `-f` | 布尔值 | False | 强制刷新缓存（不使用现有缓存） |

## 使用示例

### 基本用法

```bash
# 检测 JSON 文件中的 API 并生成 JSON 报告
python scripts/check_apis.py -i data/apis.json -o results/report.json

# 检测 CSV 文件中的 API 并生成 CSV 报告
python scripts/check_apis.py -i data/apis.csv -o results/report.csv
```

### 高级用法

```bash
# 自定义并发数、超时和重试次数
python scripts/check_apis.py -i data/apis.json -o results/report.json -c 20 -t 15 -r 2

# 强制刷新缓存（不使用缓存结果）
python scripts/check_apis.py -i data/apis.json -o results/report.json -f

# 自定义缓存过期时间为 1 小时
python scripts/check_apis.py -i data/apis.json -o results/report.json --cache-ttl 3600
```

## 输入文件格式

### JSON 格式

```json
[
  {
    "name": "API Name",
    "link": "https://api.example.com",
    "description": "API Description",
    "auth": "apiKey",
    "https": true,
    "cors": "yes"
  }
]
```

### CSV 格式

```csv
name,link,description,auth,https,cors
API Name,https://api.example.com,API Description,apiKey,True,yes
```

## 输出报告格式

### JSON 格式示例

```json
[
  {
    "name": "API Name",
    "link": "https://api.example.com",
    "status_code": 200,
    "response_time": 123.45,
    "error": null,
    "checked_at": "2023-05-20T12:34:56.123456",
    "from_cache": false
  }
]
```

### CSV 格式示例

```csv
name,link,status_code,response_time,error,checked_at,from_cache
API Name,https://api.example.com,200,123.45,,2023-05-20T12:34:56.123456,False
```

## 项目结构

```
public-apis/
├── scripts/
│   ├── check_apis.py         # 主程序文件
│   └── requirements.txt      # Python 依赖
├── tests/
│   └── test_check_apis.py    # 单元测试文件
├── data/
│   ├── apis.json            # 示例 API 数据（JSON 格式）
│   └── apis.csv             # 示例 API 数据（CSV 格式）
├── results/
│   └── *.json / *.csv       # 生成的报告文件
├── .cache/                   # 缓存目录
├── api_checker.log          # 日志文件
└── README_CHECKER.md        # 工具说明文档
```

## 缓存机制

- 缓存目录：`.cache/`
- 缓存键：使用 URL 的 MD5 哈希值
- 缓存内容：包含 API 检查结果和缓存时间
- 过期策略：根据 `--cache-ttl` 参数自动清理过期缓存
- 强制刷新：使用 `--force` 参数可忽略现有缓存并重新检测

## 日志

- 日志文件：`api_checker.log`
- 日志级别：INFO
- 日志内容包含：
  - 程序启动和结束时间
  - API 读取数量和来源
  - 检测过程中的成功和失败信息
  - 报告生成状态
  - 错误和警告信息

## 单元测试

### 运行测试

```bash
pytest tests/test_check_apis.py -v
```

### 测试覆盖

- 数据读取模块（JSON/CSV）
- 报告生成模块（JSON/CSV）
- 缓存管理器模块
- API 检查器模块（包括并发请求、重试机制）

## 使用示例

### 1. 准备输入文件

创建 `data/apis.json` 文件：

```json
[
  {
    "name": "GitHub API",
    "link": "https://api.github.com",
    "description": "GitHub REST API",
    "auth": "oauth",
    "https": true,
    "cors": "yes"
  },
  {
    "name": "JSONPlaceholder",
    "link": "https://jsonplaceholder.typicode.com",
    "description": "Fake online REST API for testing",
    "auth": "no",
    "https": true,
    "cors": "yes"
  }
]
```

### 2. 运行检测

```bash
python scripts/check_apis.py -i data/apis.json -o results/report.json
```

### 3. 查看报告

查看生成的 `results/report.json` 文件：

```json
[
  {
    "name": "GitHub API",
    "link": "https://api.github.com",
    "status_code": 200,
    "response_time": 123.45,
    "error": null,
    "checked_at": "2023-05-20T12:34:56.123456",
    "from_cache": false
  },
  {
    "name": "JSONPlaceholder",
    "link": "https://jsonplaceholder.typicode.com",
    "status_code": 200,
    "response_time": 45.67,
    "error": null,
    "checked_at": "2023-05-20T12:34:56.789012",
    "from_cache": false
  }
]
```

## 常见问题

### 1. 如何处理 HTTPS 证书验证问题？

如果遇到 SSL 证书验证错误，可以修改 `check_apis.py` 中的 `_check_single_api` 方法，在 `session.get` 中添加 `ssl=False` 参数（仅用于测试环境）。

### 2. 如何代理设置？

可以在 `aiohttp.ClientSession` 中添加代理配置，参考 aiohttp 文档。

### 3. 检测速度慢怎么办？

可以尝试调整 `--concurrency` 参数增加并发数，但注意不要设置过高导致目标服务器拒绝请求。

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！