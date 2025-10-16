# News Extractor Frontend

Vue 3 + TypeScript + Vite 构建的新闻提取器前端应用。

## 开发

```bash
# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build

# 预览生产构建
npm run preview
```

## 环境变量

创建 `.env.local` 文件：

```
VITE_API_BASE_URL=http://localhost:8000
```

## 组件说明

- `App.vue` - 主应用组件
- `UrlInput.vue` - URL 输入和平台检测
- `ExtractProgress.vue` - 提取进度显示
- `ResultViewer.vue` - 结果展示和导出
