# API 目录应用

一个极简的 React + TypeScript 应用，用于展示和搜索 API 目录。

## 功能特性

- 📋 **列表展示**：以卡片形式展示 API 信息（名称、描述、链接）
- 🔍 **即时搜索**：支持按 API 名称和描述进行实时搜索
- ⭐ **收藏功能**：可以收藏喜欢的 API，并持久化到 localStorage
- 📱 **响应式设计**：适配桌面和移动设备

## 数据来源

应用加载本地 `data/apis.json` 文件，包含以下分类的 API：

- Animals（动物）
- Books（书籍）
- Finance（金融）
- Games（游戏）
- Health（健康）
- News（新闻）

共包含 30 条 API 数据。

## 启动步骤

### 1. 安装依赖

```bash
npm install
```

### 2. 启动开发服务器

```bash
npm run dev
```

服务器将在 `http://localhost:5174/` 启动（如果 5173 端口被占用，会自动选择其他端口）。

### 3. 访问应用

在浏览器中打开 `http://localhost:5174/` 即可使用应用。

### 4. 构建生产版本

```bash
npm run build
```

构建产物将生成在 `dist` 目录。

## 使用说明

### 搜索功能

- 在顶部搜索框中输入关键词
- 搜索会实时匹配 API 名称和描述
- 支持大小写不敏感搜索

### 收藏功能

- 点击 API 卡片右上角的星形按钮可以收藏/取消收藏
- 收藏的 API 会以黄色星形显示
- 收藏数据会自动保存到浏览器的 localStorage，刷新页面后不会丢失

### 访问 API

- 点击 API 卡片底部的「访问 API」按钮
- 会在新标签页中打开 API 的官方网站

## 技术栈

- **React 18** - 用户界面库
- **TypeScript** - 类型安全的 JavaScript
- **Vite** - 快速的构建工具
- **CSS3** - 样式设计
- **localStorage** - 数据持久化

## 项目结构

```
public-apis/
├── data/
│   └── apis.json          # API 数据文件
├── src/
│   ├── App.tsx            # 主应用组件
│   ├── App.css            # 应用样式
│   ├── index.css          # 全局样式
│   └── main.tsx           # 应用入口
├── vite.config.ts         # Vite 配置
├── package.json           # 项目配置
└── README_APP.md          # 应用说明文档
```

## 自定义数据

你可以通过编辑 `data/apis.json` 文件来自定义 API 数据。文件格式如下：

```json
{
  "categories": [
    {
      "category": "分类名称",
      "apis": [
        {
          "name": "API 名称",
          "description": "API 描述",
          "link": "API 链接"
        }
      ]
    }
  ]
}
```

## 许可证

MIT License