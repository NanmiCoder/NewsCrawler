<template>
  <div class="result-viewer-new card">
    <div class="result-header">
      <h2 class="section-title">✨ 提取结果</h2>
      <div class="header-actions">
        <button class="btn btn-sm" @click="downloadFile">
          📥 下载
        </button>
        <button class="btn btn-sm" @click="copyToClipboard">
          📋 复制
        </button>
      </div>
    </div>

    <!-- 文章元信息 -->
    <div class="article-meta" v-if="result.data">
      <div class="meta-header">
        <h3 class="article-title">{{ result.data.title }}</h3>
        <span class="platform-tag">
          {{ platformNames[result.platform || ''] || result.platform }}
        </span>
      </div>

      <div class="meta-details">
        <div class="meta-item" v-if="result.data.meta_info?.author_name">
          <span class="meta-label">作者</span>
          <span class="meta-value">{{ result.data.meta_info.author_name }}</span>
        </div>
        <div class="meta-item" v-if="result.data.meta_info?.publish_time">
          <span class="meta-label">发布时间</span>
          <span class="meta-value">{{ result.data.meta_info.publish_time }}</span>
        </div>
        <div class="meta-item">
          <span class="meta-label">提取时间</span>
          <span class="meta-value">{{ formatTime(result.extracted_at) }}</span>
        </div>
      </div>

      <div class="stats-bar">
        <div class="stat-item">
          <span class="stat-icon">📝</span>
          <span class="stat-value">{{ result.data.texts?.length || 0 }}</span>
          <span class="stat-label">段落</span>
        </div>
        <div class="stat-item">
          <span class="stat-icon">🖼️</span>
          <span class="stat-value">{{ result.data.images?.length || 0 }}</span>
          <span class="stat-label">图片</span>
        </div>
        <div class="stat-item">
          <span class="stat-icon">🎬</span>
          <span class="stat-value">{{ result.data.videos?.length || 0 }}</span>
          <span class="stat-label">视频</span>
        </div>
      </div>
    </div>

    <!-- Tab 切换 -->
    <div class="tabs">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        class="tab-btn"
        :class="{ active: activeTab === tab.id }"
        @click="activeTab = tab.id"
      >
        <span class="tab-icon">{{ tab.icon }}</span>
        {{ tab.label }}
      </button>
    </div>

    <!-- Tab 内容 -->
    <div class="tab-content">
      <!-- 预览视图 -->
      <div v-if="activeTab === 'preview'" class="preview-view">
        <div class="content-blocks">
          <div
            v-for="(item, index) in result.data?.contents"
            :key="index"
            class="content-block"
            :class="`content-${item.type}`"
          >
            <template v-if="item.type === 'text'">
              <p class="text-content">{{ item.content }}</p>
            </template>
            <template v-else-if="item.type === 'image'">
              <div class="image-wrapper">
                <img
                  :src="getProxiedImageUrl(item.content)"
                  :alt="item.desc || '图片'"
                  loading="lazy"
                  @error="handleImageError"
                />
              </div>
            </template>
            <template v-else-if="item.type === 'video'">
              <div class="video-wrapper">
                <a :href="item.content" target="_blank" class="video-link">
                  🎬 查看视频: {{ item.content }}
                </a>
              </div>
            </template>
          </div>
        </div>
      </div>

      <!-- Markdown 视图 -->
      <div v-else-if="activeTab === 'markdown'" class="markdown-view">
        <div class="markdown-preview" v-html="formattedMarkdown"></div>
      </div>

      <!-- JSON 视图 -->
      <div v-else-if="activeTab === 'json'" class="json-view">
        <pre class="code-block"><code class="language-json" v-html="highlightedJson"></code></pre>
      </div>

      <!-- 图片视图 -->
      <div v-else-if="activeTab === 'images'" class="images-view">
        <div v-if="result.data?.images && result.data.images.length > 0" class="images-grid">
          <div v-for="(img, index) in result.data.images" :key="index" class="image-item">
            <img
              :src="getProxiedImageUrl(img)"
              :alt="`图片 ${index + 1}`"
              loading="lazy"
              @error="handleImageError"
            />
            <div class="image-overlay">
              <a :href="img" target="_blank" class="btn-view-full">查看原图</a>
            </div>
          </div>
        </div>
        <div v-else class="empty-state">
          <span class="empty-icon">🖼️</span>
          <p>该文章没有图片</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { ExtractResponse } from '@/types'
import hljs from 'highlight.js/lib/core'
import json from 'highlight.js/lib/languages/json'
import 'highlight.js/styles/github-dark.css'

// 注册 JSON 语言
hljs.registerLanguage('json', json)

const props = defineProps<{
  result: ExtractResponse
}>()

const activeTab = ref('preview')

const tabs = [
  { id: 'preview', label: '预览', icon: '👁️' },
  { id: 'markdown', label: 'Markdown', icon: '📝' },
  { id: 'json', label: 'JSON', icon: '{ }' },
  { id: 'images', label: '图片', icon: '🖼️' }
]

const platformNames: Record<string, string> = {
  wechat: '微信公众号',
  toutiao: '今日头条',
  detik: 'Detik News',
  naver: 'Naver Blog',
  lenny: "Lenny's Newsletter",
  quora: 'Quora'
}

const formattedJson = computed(() => {
  return JSON.stringify(props.result.data, null, 2)
})

const highlightedJson = computed(() => {
  const jsonString = formattedJson.value
  return hljs.highlight(jsonString, { language: 'json' }).value
})

const formattedMarkdown = computed(() => {
  if (props.result.markdown) {
    let html = props.result.markdown

    // 先处理图片（需要代理URL）
    html = html.replace(/!\[(.*?)\]\((.*?)\)/gim, (match, alt, url) => {
      const proxiedUrl = getProxiedImageUrl(url)
      return `<img src="${proxiedUrl}" alt="${alt}" style="max-width: 100%; height: auto; margin: 1rem 0;" onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjMwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iNDAwIiBoZWlnaHQ9IjMwMCIgZmlsbD0iI2YzZjRmNiIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMTgiIGZpbGw9IiM5Y2EzYWYiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuM2VtIj7lm77niYfliqDovb3lpLHotKU8L3RleHQ+PC9zdmc+'" />`
    })

    // 然后处理链接
    html = html.replace(/\[(.*?)\]\((.*?)\)/gim, '<a href="$2" target="_blank" rel="noopener">$1</a>')

    // 处理标题
    html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>')
    html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>')
    html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>')

    // 处理粗体
    html = html.replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>')

    // 处理分隔线
    html = html.replace(/^---$/gim, '<hr style="margin: 1.5rem 0; border: none; border-top: 1px solid var(--border-color);" />')

    // 处理换行
    html = html.replace(/\n/gim, '<br>')

    return html
  }
  return ''
})

const formatTime = (isoString: string) => {
  const date = new Date(isoString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const downloadFile = () => {
  let content = ''
  let filename = ''

  if (activeTab.value === 'json') {
    content = formattedJson.value
    filename = `${props.result.data?.news_id || 'export'}.json`
  } else if (activeTab.value === 'markdown') {
    content = props.result.markdown || ''
    filename = `${props.result.data?.news_id || 'export'}.md`
  } else {
    content = props.result.data?.texts?.join('\n\n') || ''
    filename = `${props.result.data?.news_id || 'export'}.txt`
  }

  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}

const copyToClipboard = async () => {
  let content = ''

  if (activeTab.value === 'json') {
    content = formattedJson.value
  } else if (activeTab.value === 'markdown') {
    content = props.result.markdown || ''
  } else {
    content = props.result.data?.texts?.join('\n\n') || ''
  }

  try {
    await navigator.clipboard.writeText(content)
    alert('✓ 已复制到剪贴板')
  } catch (error) {
    alert('✗ 复制失败，请手动复制')
  }
}

const getProxiedImageUrl = (originalUrl: string): string => {
  // 检查是否是微信公众号图片（mmbiz.qpic.cn 或 mmbiz.qlogo.cn）
  if (originalUrl.includes('mmbiz.qpic.cn') || originalUrl.includes('mmbiz.qlogo.cn')) {
    // 使用后端代理
    return `/api/proxy/image?url=${encodeURIComponent(originalUrl)}`
  }
  // 其他图片直接返回原URL
  return originalUrl
}

const handleImageError = (event: Event) => {
  const img = event.target as HTMLImageElement
  // 图片加载失败时，显示占位图
  img.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjMwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iNDAwIiBoZWlnaHQ9IjMwMCIgZmlsbD0iI2YzZjRmNiIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMTgiIGZpbGw9IiM5Y2EzYWYiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuM2VtIj7lm77niYfliqDovb3lpLHotKU8L3RleHQ+PC9zdmc+'
  img.alt = '图片加载失败'
}
</script>

<style scoped>
.result-viewer-new {
  animation: fadeIn 0.3s ease-out;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.section-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 0.5rem;
}

.btn-sm {
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
}

.article-meta {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.05), rgba(147, 51, 234, 0.05));
  padding: 1.5rem;
  border-radius: 0.75rem;
  margin-bottom: 1.5rem;
  border: 1px solid rgba(59, 130, 246, 0.2);
}

.meta-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1rem;
}

.article-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
  flex: 1;
  line-height: 1.4;
}

.platform-tag {
  padding: 0.375rem 0.75rem;
  background: var(--primary-color);
  color: white;
  border-radius: 1rem;
  font-size: 0.75rem;
  font-weight: 600;
  white-space: nowrap;
  flex-shrink: 0;
}

.meta-details {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 1rem;
}

.meta-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.meta-label {
  font-size: 0.75rem;
  color: var(--text-secondary);
  text-transform: uppercase;
  font-weight: 600;
}

.meta-value {
  font-size: 0.95rem;
  color: var(--text-primary);
}

.stats-bar {
  display: flex;
  gap: 2rem;
  padding-top: 1rem;
  border-top: 1px solid rgba(0, 0, 0, 0.1);
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.stat-icon {
  font-size: 1.25rem;
}

.stat-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--primary-color);
}

.stat-label {
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.tabs {
  display: flex;
  gap: 0.5rem;
  border-bottom: 2px solid var(--border-color);
  margin-bottom: 1.5rem;
  overflow-x: auto;
}

.tab-btn {
  padding: 0.75rem 1.5rem;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  font-size: 0.95rem;
  font-weight: 500;
  cursor: pointer;
  position: relative;
  transition: all 0.2s;
  white-space: nowrap;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.tab-btn:hover {
  color: var(--primary-color);
  background: rgba(59, 130, 246, 0.05);
}

.tab-btn.active {
  color: var(--primary-color);
  font-weight: 600;
}

.tab-btn.active::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 0;
  right: 0;
  height: 2px;
  background: var(--primary-color);
}

.tab-icon {
  font-size: 1.1rem;
}

.tab-content {
  min-height: 400px;
}

.preview-view {
  animation: fadeIn 0.3s ease-out;
}

.content-blocks {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.content-block {
  animation: slideUp 0.3s ease-out;
}

.text-content {
  line-height: 1.8;
  color: var(--text-primary);
  margin: 0;
  font-size: 1rem;
}

.image-wrapper {
  border-radius: 0.5rem;
  overflow: hidden;
  border: 1px solid var(--border-color);
}

.image-wrapper img {
  width: 100%;
  height: auto;
  display: block;
}

.video-link {
  display: block;
  padding: 1rem;
  background: var(--bg-color);
  border: 1px solid var(--border-color);
  border-radius: 0.5rem;
  color: var(--primary-color);
  text-decoration: none;
  transition: all 0.2s;
}

.video-link:hover {
  background: rgba(59, 130, 246, 0.05);
  border-color: var(--primary-color);
}

.markdown-view,
.json-view {
  animation: fadeIn 0.3s ease-out;
}

.markdown-preview {
  padding: 1.5rem;
  background: var(--bg-color);
  border-radius: 0.5rem;
  line-height: 1.8;
  border: 1px solid var(--border-color);
}

.markdown-preview :deep(h1),
.markdown-preview :deep(h2),
.markdown-preview :deep(h3) {
  margin-top: 1.5rem;
  margin-bottom: 0.75rem;
  font-weight: 600;
  color: var(--text-primary);
}

.markdown-preview :deep(img) {
  border-radius: 0.5rem;
}

.code-block {
  padding: 0;
  background: #0d1117;
  border: 1px solid var(--border-color);
  border-radius: 0.5rem;
  overflow-x: auto;
  margin: 0;
}

.code-block code {
  display: block;
  padding: 1.5rem;
  font-family: 'Monaco', 'Menlo', 'Consolas', 'Courier New', monospace;
  font-size: 0.875rem;
  line-height: 1.6;
  background: transparent;
  color: #e6edf3;
}

/* 覆盖 highlight.js 的一些默认样式 */
.code-block code :deep(.hljs-attr) {
  color: #79c0ff;
}

.code-block code :deep(.hljs-string) {
  color: #a5d6ff;
}

.code-block code :deep(.hljs-number) {
  color: #79c0ff;
}

.code-block code :deep(.hljs-literal) {
  color: #ff7b72;
}

.code-block code :deep(.hljs-punctuation) {
  color: #e6edf3;
}

.images-view {
  animation: fadeIn 0.3s ease-out;
}

.images-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 1rem;
}

.image-item {
  position: relative;
  border-radius: 0.5rem;
  overflow: hidden;
  border: 1px solid var(--border-color);
  aspect-ratio: 16 / 9;
  background: var(--bg-color);
}

.image-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s;
}

.image-item:hover img {
  transform: scale(1.05);
}

.image-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s;
}

.image-item:hover .image-overlay {
  opacity: 1;
}

.btn-view-full {
  padding: 0.5rem 1rem;
  background: white;
  color: var(--text-primary);
  border-radius: 0.375rem;
  text-decoration: none;
  font-size: 0.875rem;
  font-weight: 500;
}

.empty-state {
  text-align: center;
  padding: 3rem 1rem;
  color: var(--text-secondary);
}

.empty-icon {
  font-size: 3rem;
  display: block;
  margin-bottom: 1rem;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
