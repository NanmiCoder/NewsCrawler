<template>
  <div class="result-container card">
    <div class="result-header">
      <h2 class="section-title">📄 提取结果</h2>

      <div class="format-tabs">
        <button
          class="format-tab"
          :class="{ active: format === 'json' }"
          @click="emit('format-change', 'json')"
        >
          JSON
        </button>
        <button
          class="format-tab"
          :class="{ active: format === 'markdown' }"
          @click="emit('format-change', 'markdown')"
        >
          Markdown
        </button>
      </div>
    </div>

    <div class="meta-info" v-if="result.data">
      <div class="meta-item">
        <strong>标题:</strong>
        <span>{{ result.data.title }}</span>
      </div>
      <div class="meta-item">
        <strong>作者:</strong>
        <span>{{ result.data.meta_info.author_name || '未知' }}</span>
      </div>
      <div class="meta-item">
        <strong>发布时间:</strong>
        <span>{{ result.data.meta_info.publish_time || '未知' }}</span>
      </div>
      <div class="meta-item">
        <strong>平台:</strong>
        <span>{{ platformNames[result.platform || ''] || result.platform }}</span>
      </div>
    </div>

    <div class="content-preview">
      <pre v-if="format === 'json'" class="code-block">{{ formattedJson }}</pre>
      <div v-else class="markdown-preview" v-html="formattedMarkdown"></div>
    </div>

    <div class="media-stats" v-if="result.data">
      <span class="stat-item">
        📷 图片 {{ result.data.images?.length || 0 }} 张
      </span>
      <span class="stat-item">
        🎬 视频 {{ result.data.videos?.length || 0 }} 个
      </span>
    </div>

    <div class="action-buttons">
      <button class="btn btn-primary" @click="downloadFile">
        📥 下载 {{ format.toUpperCase() }}
      </button>
      <button class="btn" @click="copyToClipboard">
        📋 复制内容
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ExtractResponse } from '@/types'

const props = defineProps<{
  result: ExtractResponse
  format: 'json' | 'markdown'
}>()

const emit = defineEmits<{
  'format-change': [format: 'json' | 'markdown']
}>()

const platformNames: Record<string, string> = {
  wechat: '微信公众号',
  toutiao: '今日头条',
  detik: 'Detik News',
  naver: 'Naver News',
  lenny: "Lenny's Newsletter",
  quora: 'Quora'
}

const formattedJson = computed(() => {
  return JSON.stringify(props.result.data, null, 2)
})

const formattedMarkdown = computed(() => {
  if (props.result.markdown) {
    // 简单的 Markdown 转 HTML
    return props.result.markdown
      // 图片: ![alt](url)
      .replace(/!\[(.*?)\]\((.*?)\)/gim, '<img src="$2" alt="$1" style="max-width: 100%; height: auto; margin: 1rem 0;" />')
      // 链接: [text](url)
      .replace(/\[(.*?)\]\((.*?)\)/gim, '<a href="$2" target="_blank" rel="noopener">$1</a>')
      // 标题
      .replace(/^### (.*$)/gim, '<h3>$1</h3>')
      .replace(/^## (.*$)/gim, '<h2>$1</h2>')
      .replace(/^# (.*$)/gim, '<h1>$1</h1>')
      // 粗体
      .replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>')
      // 分隔线
      .replace(/^---$/gim, '<hr style="margin: 1.5rem 0; border: none; border-top: 1px solid var(--border-color);" />')
      // 换行
      .replace(/\n/gim, '<br>')
  }
  return ''
})

const downloadFile = () => {
  const content = props.format === 'json' ? formattedJson.value : props.result.markdown || ''
  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `news_${props.result.data?.news_id || 'export'}.${props.format}`
  link.click()
  URL.revokeObjectURL(url)
}

const copyToClipboard = async () => {
  const content = props.format === 'json' ? formattedJson.value : props.result.markdown || ''
  try {
    await navigator.clipboard.writeText(content)
    alert('已复制到剪贴板')
  } catch (error) {
    alert('复制失败，请手动复制')
  }
}
</script>

<style scoped>
.result-container {
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

.format-tabs {
  display: flex;
  gap: 0.5rem;
  background-color: var(--bg-color);
  padding: 0.25rem;
  border-radius: 0.375rem;
  border: 1px solid var(--border-color);
}

.format-tab {
  padding: 0.5rem 1rem;
  border: none;
  background: transparent;
  border-radius: 0.25rem;
  cursor: pointer;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-secondary);
  transition: all 0.2s;
}

.format-tab.active {
  background-color: var(--primary-color);
  color: white;
}

.meta-info {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 0.75rem;
  margin-bottom: 1.5rem;
  padding: 1rem;
  background-color: var(--bg-color);
  border-radius: 0.375rem;
  border: 1px solid var(--border-color);
}

.meta-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.meta-item strong {
  font-size: 0.75rem;
  color: var(--text-secondary);
  text-transform: uppercase;
}

.meta-item span {
  font-size: 0.875rem;
  color: var(--text-primary);
}

.content-preview {
  max-height: 500px;
  overflow-y: auto;
  margin-bottom: 1.5rem;
  border: 1px solid var(--border-color);
  border-radius: 0.375rem;
}

.code-block {
  padding: 1rem;
  background-color: var(--bg-color);
  font-family: 'Monaco', 'Consolas', monospace;
  font-size: 0.875rem;
  line-height: 1.5;
  color: var(--text-primary);
  overflow-x: auto;
  margin: 0;
}

.markdown-preview {
  padding: 1.5rem;
  background-color: var(--bg-color);
  line-height: 1.8;
}

.markdown-preview :deep(h1),
.markdown-preview :deep(h2),
.markdown-preview :deep(h3) {
  margin-top: 1.5rem;
  margin-bottom: 0.75rem;
  font-weight: 600;
}

.media-stats {
  display: flex;
  gap: 1.5rem;
  margin-bottom: 1.5rem;
  padding: 0.75rem 1rem;
  background-color: var(--bg-color);
  border-radius: 0.375rem;
  border: 1px solid var(--border-color);
}

.stat-item {
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.action-buttons {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}
</style>
