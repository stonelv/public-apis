# Public APIs Client

一个极简的 React + TypeScript 应用，展示公共 API 列表并提供搜索和收藏功能。

## 功能特性

1. **列表展示**: 以卡片形式展示 API 的名称、描述和官网链接
2. **即时搜索**: 支持按 API 名称和描述实时搜索过滤
3. **收藏功能**: 
   - 点击星标按钮收藏/取消收藏 API
   - 收藏数据持久化存储在 localStorage
   - 刷新页面后收藏状态不会丢失

## 快速开始

### 1. 安装依赖

```bash
npm install
```

### 2. 启动开发服务器

```bash
npm run dev
```

应用将在 `http://localhost:3000` 启动。

### 3. 构建生产版本

```bash
npm run build
```

### 4. 预览生产构建

```bash
npm run preview
```

## 项目结构

```
├── data/
│   └── apis.json          # API 数据源（33条公共API）
├── src/
│   ├── App.tsx            # 主应用组件
│   ├── main.tsx           # 应用入口
│   ├── index.css          # 全局样式
│   └── types.ts           # TypeScript 类型定义
├── index.html             # HTML 模板
├── package.json           # 项目依赖
├── tsconfig.json          # TypeScript 配置
├── tsconfig.node.json     # Vite 专用 TypeScript 配置
└── vite.config.ts         # Vite 配置
```

## 使用说明

### 搜索

在顶部搜索框中输入关键词，系统会实时根据 API 名称和描述进行过滤。

### 收藏

1. 点击卡片右上角的空心星标即可收藏该 API
2. 收藏后星标会变成实心黄色
3. 再次点击可取消收藏
4. 收藏数据会自动保存到浏览器 localStorage，下次打开页面时会自动恢复

## 技术栈

- **React 18**: UI 框架
- **TypeScript**: 类型安全
- **Vite**: 构建工具
- **CSS3**: 原生 CSS 样式
