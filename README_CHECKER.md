# API 可用性检测工具

一个用于并发检测公共API可用性的Python CLI工具，支持JSON/CSV输入输出、缓存、重试策略等功能。

## 功能特性

- 🔄 **并发检测**: 支持并发请求多个API，提高检测效率
- 📁 **多种格式**: 支持JSON和CSV格式的输入输出
- 💾 **本地缓存**: 智能缓存机制，避免重复请求
- 🔄 **重试策略**: 可配置的重试次数和退避策略
- ⏱️ **超时控制**: 可配置的请求超时时间
- 📊 **详细报告**: 生成包含状态码、响应时间、错误信息的详细报告
- 📈 **统计信息**: 生成检测统计报告
- 📝 **日志记录**: 详细的日志记录

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 基本用法

```bash
python scripts/check_apis.py --input data/sample_apis.json --output results.json
```

### 命令行参数

```
--input, -i       输入文件路径 (JSON或CSV格式) [必填]
--output, -o      输出文件路径 (JSON或CSV格式) [必填]
--concurrency, -c 并发请求数 (默认: 10)
--timeout, -t     超时时间(秒) (默认: 10)
--retries, -r     重试次数 (默认: 3)
--backoff-factor  退避因子 (默认: 0.5)
--cache-ttl       缓存TTL(秒) (默认: 3600)
--force, -f       强制刷新缓存 (忽略缓存TTL)
```

### 示例

1. **使用JSON输入输出**:
```bash
python scripts/check_apis.py --input data/sample_apis.json --output results.json
```

2. **使用CSV输入输出**:
```bash
python scripts/check_apis.py --input data/sample_apis.csv --output results.csv
```

3. **自定义并发数和超时**:
```bash
python scripts/check_apis.py --input data/sample_apis.json --output results.json --concurrency 20 --timeout 15
```

4. **强制刷新缓存**:
```bash
python scripts/check_apis.py --input data/sample_apis.json --output results.json --force
```

5. **自定义重试策略**:
```bash
python scripts/check_apis.py --input data/sample_apis.json --output results.json --retries 5 --backoff-factor 1.0
```

## 输入格式

### JSON格式
```json
[
  {
    "name": "API名称",
    "link": "API链接",
    "category": "分类(可选)",
    "description": "描述(可选)"
  },
  ...
]
```

### CSV格式
```csv
name,link,category,description
API名称,API链接,分类,描述
...
```

## 输出格式

### JSON格式
```json
[
  {
    "name": "API名称",
    "link": "API链接",
    "status_code": 200,
    "response_time_ms": 150.5,
    "error_message": null,
    "check_time": "2023-01-01T12:00:00",
    "category": "分类",
    "description": "描述"
  },
  ...
]
```

### CSV格式
```csv
name,link,status_code,response_time_ms,error_message,check_time,category,description
API名称,API链接,200,150.5,,2023-01-01T12:00:00,分类,描述
...
```

## 缓存机制

- 缓存目录: `cache/`
- 缓存键: 使用API链接的MD5哈希值
- 缓存TTL: 默认3600秒(1小时)
- 缓存文件: 每个API对应一个JSON文件

## 重试策略

- 重试次数: 默认3次
- 退避策略: 指数退避，默认退避因子0.5
- 重试状态码: 429, 500, 502, 503, 504
- 重试方法: HEAD, GET, OPTIONS

## 运行测试

```bash
pytest tests/test_check_apis.py -v
```

## 项目结构

```
public-apis/
├── data/                # 示例数据文件
│   ├── sample_apis.json
│   └── sample_apis.csv
├── scripts/             # 脚本文件
│   └── check_apis.py    # 主CLI工具
├── tests/               # 测试文件
│   └── test_check_apis.py
├── cache/               # 缓存目录(自动创建)
├── results/             # 结果目录(自动创建)
├── requirements.txt     # 依赖列表
└── README_CHECKER.md    # 本文件
```

## 输出示例

### 控制台输出

```
2025-12-02 17:22:27,618 - INFO - 开始API检测...
2025-12-02 17:22:27,622 - INFO - 共加载 5 个API
2025-12-02 17:22:30,080 - INFO - API JSONPlaceholder Users - 状态码: 200, 响应时间: 2453.06ms
2025-12-02 17:22:30,083 - INFO - API JSONPlaceholder Comments - 状态码: 200, 响应时间: 2454.93ms
2025-12-02 17:22:30,083 - INFO - API Random User Generator - 状态码: 200, 响应时间: 2453.08ms
2025-12-02 17:22:30,084 - INFO - API JSONPlaceholder - 状态码: 200, 响应时间: 2457.44ms
2025-12-02 17:22:30,225 - INFO - API GitHub API - 状态码: 200, 响应时间: 2599.29ms
2025-12-02 17:22:30,230 - INFO - 结果已保存到: results/sample_results.json
==================================================
检测统计:
总API数: 5
成功: 5 (100.0%)
失败: 0 (0.0%)
平均响应时间: 2483.56ms
==================================================
2025-12-02 17:22:30,249 - INFO - API检测完成!
```

### 输出文件示例

```json
[
  {
    "name": "JSONPlaceholder Users",
    "link": "https://jsonplaceholder.typicode.com/users",
    "status_code": 200,
    "response_time_ms": 2453.06,
    "error_message": null,
    "check_time": "2025-12-02T17:22:27.625678",
    "category": "Fake Data",
    "description": "Free fake API for testing and prototyping"
  },
  ...
]
```

## 日志文件

日志会同时输出到控制台和 `api_checker.log` 文件。

## 注意事项

1. 确保输入文件格式正确，包含必要的字段
2. 并发数不宜设置过高，避免被目标网站限制
3. 合理设置缓存TTL，避免频繁请求相同API
4. 对于不稳定的网络环境，适当增加超时时间和重试次数

## 许可证

MIT License
