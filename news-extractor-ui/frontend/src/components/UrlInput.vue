<template>
  <div class="url-input-container card">
    <h2 class="section-title">🔗 输入新闻链接</h2>

    <div class="input-group">
      <input
        v-model="url"
        type="text"
        class="input url-input"
        placeholder="请输入新闻链接，如: https://mp.weixin.qq.com/s/xxxxx"
        @keyup.enter="handleExtract"
      />
    </div>

    <div class="platform-detected" v-if="detectedPlatform">
      <span class="detected-label">自动识别:</span>
      <span class="platform-badge">{{ platformName }} ✓</span>
    </div>

    <div class="action-bar">
      <div class="format-selector">
        <label>
          <input type="radio" value="json" v-model="selectedFormat" />
          <span>JSON</span>
        </label>
        <label>
          <input type="radio" value="markdown" v-model="selectedFormat" />
          <span>Markdown</span>
        </label>
      </div>

      <button
        class="btn btn-primary extract-btn"
        @click="handleExtract"
        :disabled="!url || loading"
      >
        <span v-if="loading">提取中...</span>
        <span v-else>开始提取</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

const props = defineProps<{
  loading: boolean
}>()

const emit = defineEmits<{
  extract: [url: string, format: 'json' | 'markdown']
}>()

const url = ref('')
const selectedFormat = ref<'json' | 'markdown'>('json')
const detectedPlatform = ref('')
const platformName = ref('')

const platformMap: Record<string, string> = {
  'mp.weixin.qq.com': '微信公众号',
  'toutiao.com': '今日头条',
  'detik.com': 'Detik News',
  'naver.com': 'Naver News',
  'lennysnewsletter.com': "Lenny's Newsletter",
  'quora.com': 'Quora'
}

// 监听 URL 变化，自动检测平台
watch(url, (newUrl) => {
  if (!newUrl) {
    detectedPlatform.value = ''
    platformName.value = ''
    return
  }

  for (const [domain, name] of Object.entries(platformMap)) {
    if (newUrl.includes(domain)) {
      detectedPlatform.value = domain
      platformName.value = name
      return
    }
  }

  detectedPlatform.value = ''
  platformName.value = ''
})

const handleExtract = () => {
  if (!url.value || props.loading) return
  emit('extract', url.value, selectedFormat.value)
}
</script>

<style scoped>
.url-input-container {
  animation: fadeIn 0.3s ease-out;
}

.section-title {
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: 1rem;
  color: var(--text-primary);
}

.input-group {
  margin-bottom: 1rem;
}

.url-input {
  font-size: 0.95rem;
}

.platform-detected {
  padding: 0.75rem 1rem;
  background-color: rgba(16, 185, 129, 0.1);
  border-radius: 0.375rem;
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  animation: fadeIn 0.3s ease-out;
}

.detected-label {
  color: var(--text-secondary);
  font-size: 0.875rem;
}

.platform-badge {
  color: var(--success-color);
  font-weight: 600;
  font-size: 0.875rem;
}

.action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1rem;
}

.format-selector {
  display: flex;
  gap: 1.5rem;
}

.format-selector label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.format-selector input[type="radio"] {
  cursor: pointer;
}

.extract-btn {
  padding: 0.75rem 2rem;
  font-size: 1rem;
}
</style>
