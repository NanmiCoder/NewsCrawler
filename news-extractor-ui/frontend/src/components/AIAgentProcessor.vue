<template>
  <div class="ai-processor card">
    <div class="processor-header">
      <h3 class="processor-title">✨ AI Content Processing</h3>
      <div class="config-status" v-if="llmConfig">
        <span class="status-badge">{{ llmConfig.provider }}</span>
        <span class="status-model">{{ llmConfig.model_name }}</span>
      </div>
    </div>

    <!-- Config Required Warning -->
    <div v-if="!llmConfig" class="warning-box">
      <div class="warning-icon">⚠️</div>
      <div class="warning-content">
        <div class="warning-title">Configuration Required</div>
        <div class="warning-message">
          Please configure your LLM settings above before using the AI Agent.
        </div>
      </div>
    </div>

    <div v-else>
      <!-- Task Selection -->
      <div class="task-section">
        <h4 class="section-subtitle">Select Task</h4>
        <div class="task-grid">
          <div
            v-for="task in tasks"
            :key="task.id"
            class="task-card"
            :class="{ active: selectedTask === task.id }"
            @click="selectedTask = task.id"
          >
            <div class="task-icon">{{ task.icon }}</div>
            <div class="task-name">{{ task.name }}</div>
            <div class="task-desc">{{ task.description }}</div>
          </div>
        </div>
      </div>

      <!-- Content Input -->
      <div class="content-section">
        <h4 class="section-subtitle">Content to Process</h4>
        <div class="content-source-tabs">
          <button
            class="source-tab"
            :class="{ active: contentSource === 'extracted' }"
            @click="contentSource = 'extracted'"
          >
            From Extracted News
          </button>
          <button
            class="source-tab"
            :class="{ active: contentSource === 'custom' }"
            @click="contentSource = 'custom'"
          >
            Custom Content
          </button>
        </div>

        <div v-if="contentSource === 'extracted'" class="extracted-preview">
          <div class="preview-meta">
            <span class="preview-label">Content Preview:</span>
            <span class="preview-count">{{ contentPreview.length }} characters</span>
          </div>
          <div class="preview-text">{{ contentPreview }}</div>
        </div>

        <textarea
          v-else
          v-model="customContent"
          class="content-textarea"
          placeholder="Enter your custom content here..."
          rows="8"
        ></textarea>

        <!-- Image Options (for vision models) -->
        <div v-if="supportsVision && extractedImages.length > 0" class="image-options">
          <label class="checkbox-label">
            <input type="checkbox" v-model="includeImages" />
            <span>Include {{ extractedImages.length }} images for vision analysis</span>
          </label>
        </div>
      </div>

      <!-- Process Button -->
      <div class="process-actions">
        <button
          class="btn btn-primary btn-lg"
          :disabled="!canProcess || processing"
          @click="processContent"
        >
          <span v-if="!processing">🚀</span>
          <span v-else class="spinner">⏳</span>
          <span>{{ processing ? 'Processing...' : 'Process with AI' }}</span>
        </button>
      </div>

      <!-- Results -->
      <div v-if="result" class="results-section">
        <div class="results-header">
          <h4 class="section-subtitle">✅ Results</h4>
          <div class="results-actions">
            <button class="btn-icon" @click="copyResult" title="Copy">📋</button>
            <button class="btn-icon" @click="downloadResult" title="Download">📥</button>
          </div>
        </div>

        <div class="result-box">
          <div class="result-content">{{ result.result }}</div>
        </div>

        <div class="result-meta">
          <div class="meta-item">
            <span class="meta-label">Provider:</span>
            <span class="meta-value">{{ result.provider }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">Model:</span>
            <span class="meta-value">{{ result.model }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">Task:</span>
            <span class="meta-value">{{ result.task_type }}</span>
          </div>
        </div>
      </div>

      <!-- Error Display -->
      <div v-if="error" class="error-box">
        <div class="error-icon">❌</div>
        <div class="error-content">
          <div class="error-title">Processing Failed</div>
          <div class="error-message">{{ error }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { getAgentTasks, processWithAgent, getAgentProviders } from '@/services/api'
import type { LLMConfig, TaskInfo, AgentResponse, NewsItem, LLMProviderInfo } from '@/types'

const props = defineProps<{
  llmConfig?: LLMConfig
  newsData?: NewsItem
}>()

const tasks = ref<TaskInfo[]>([])
const selectedTask = ref<string>('')
const contentSource = ref<'extracted' | 'custom'>('extracted')
const customContent = ref('')
const includeImages = ref(false)
const processing = ref(false)
const result = ref<AgentResponse | null>(null)
const error = ref<string>('')
const providers = ref<LLMProviderInfo[]>([])

const contentPreview = computed(() => {
  if (!props.newsData) return ''
  const text = props.newsData.texts.join('\n\n')
  return text.length > 500 ? text.substring(0, 500) + '...' : text
})

const extractedImages = computed(() => {
  return props.newsData?.images || []
})

const supportsVision = computed(() => {
  if (!props.llmConfig) return false
  const provider = providers.value.find(p => p.id === props.llmConfig!.provider)
  return provider?.supports_vision || false
})

const canProcess = computed(() => {
  const hasContent = contentSource.value === 'extracted'
    ? !!props.newsData
    : !!customContent.value.trim()

  return hasContent && !!selectedTask.value && !processing.value
})

const processContent = async () => {
  if (!canProcess.value || !props.llmConfig) return

  processing.value = true
  error.value = ''
  result.value = null

  try {
    const content = contentSource.value === 'extracted'
      ? props.newsData!.texts.join('\n\n')
      : customContent.value

    const images = includeImages.value && supportsVision.value
      ? extractedImages.value.slice(0, 5)  // Limit to 5 images
      : undefined

    const response = await processWithAgent({
      llm_config: props.llmConfig,
      task_type: selectedTask.value as any,
      content: content,
      images: images,
    })

    if (response.status === 'success') {
      result.value = response
    } else {
      error.value = response.error?.message || 'Unknown error occurred'
    }
  } catch (e: any) {
    error.value = e.message || 'Failed to process content'
  } finally {
    processing.value = false
  }
}

const copyResult = async () => {
  if (!result.value?.result) return

  try {
    await navigator.clipboard.writeText(result.value.result)
    alert('✓ Result copied to clipboard')
  } catch (e) {
    alert('✗ Failed to copy')
  }
}

const downloadResult = () => {
  if (!result.value?.result) return

  const blob = new Blob([result.value.result], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `ai_result_${result.value.task_type}_${Date.now()}.txt`
  link.click()
  URL.revokeObjectURL(url)
}

// Watch for config changes and reset result
watch(() => props.llmConfig, () => {
  result.value = null
  error.value = ''
})

onMounted(async () => {
  try {
    const [tasksResponse, providersResponse] = await Promise.all([
      getAgentTasks(),
      getAgentProviders()
    ])
    tasks.value = tasksResponse.tasks
    providers.value = providersResponse.providers

    // Select first task by default
    if (tasks.value.length > 0) {
      selectedTask.value = tasks.value[0].id
    }
  } catch (e) {
    console.error('Failed to load agent configuration:', e)
  }
})
</script>

<style scoped>
.ai-processor {
  animation: fadeIn 0.3s ease-out;
}

.processor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.processor-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--text-100);
  margin: 0;
}

.config-status {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.status-badge {
  padding: 0.375rem 0.75rem;
  background: linear-gradient(135deg, var(--primary-200), var(--primary-100));
  color: white;
  border-radius: 8px;
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
}

.status-model {
  font-size: 0.875rem;
  color: var(--text-200);
  font-weight: 500;
}

.warning-box, .error-box {
  display: flex;
  gap: 1rem;
  padding: 1.5rem;
  border-radius: 12px;
  margin-bottom: 1.5rem;
}

.warning-box {
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.1), rgba(251, 191, 36, 0.1));
  border: 2px solid rgba(245, 158, 11, 0.3);
}

.error-box {
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.1), rgba(252, 165, 165, 0.1));
  border: 2px solid rgba(239, 68, 68, 0.3);
}

.warning-icon, .error-icon {
  font-size: 2rem;
}

.warning-content, .error-content {
  flex: 1;
}

.warning-title, .error-title {
  font-weight: 700;
  font-size: 1rem;
  margin-bottom: 0.5rem;
  color: var(--text-100);
}

.warning-message, .error-message {
  font-size: 0.95rem;
  color: var(--text-200);
  line-height: 1.5;
}

.task-section, .content-section {
  margin-bottom: 2rem;
}

.section-subtitle {
  font-size: 1rem;
  font-weight: 700;
  color: var(--text-100);
  margin-bottom: 1rem;
}

.task-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
}

.task-card {
  padding: 1.25rem;
  border: 2px solid var(--border-color);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  text-align: center;
}

.task-card:hover {
  border-color: var(--primary-200);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(253, 87, 50, 0.15);
}

.task-card.active {
  border-color: var(--primary-200);
  background: linear-gradient(135deg, rgba(253, 87, 50, 0.1), rgba(255, 183, 135, 0.1));
}

.task-icon {
  font-size: 2rem;
  margin-bottom: 0.5rem;
}

.task-name {
  font-weight: 700;
  color: var(--text-100);
  margin-bottom: 0.5rem;
}

.task-desc {
  font-size: 0.85rem;
  color: var(--text-200);
  line-height: 1.4;
}

.content-source-tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.source-tab {
  flex: 1;
  padding: 0.75rem;
  border: 2px solid var(--border-color);
  border-radius: 8px;
  background: white;
  color: var(--text-200);
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.source-tab:hover {
  border-color: var(--primary-200);
  color: var(--primary-200);
}

.source-tab.active {
  border-color: var(--primary-200);
  background: linear-gradient(135deg, rgba(253, 87, 50, 0.1), rgba(255, 183, 135, 0.1));
  color: var(--primary-200);
}

.extracted-preview {
  padding: 1rem;
  background: var(--bg-100);
  border: 2px solid var(--border-color);
  border-radius: 12px;
}

.preview-meta {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.75rem;
  font-size: 0.875rem;
}

.preview-label {
  font-weight: 600;
  color: var(--text-100);
}

.preview-count {
  color: var(--text-200);
}

.preview-text {
  color: var(--text-200);
  line-height: 1.6;
  max-height: 150px;
  overflow-y: auto;
}

.content-textarea {
  width: 100%;
  padding: 1rem;
  border: 2px solid var(--border-color);
  border-radius: 12px;
  font-size: 0.95rem;
  font-family: inherit;
  resize: vertical;
  transition: all 0.2s;
}

.content-textarea:focus {
  outline: none;
  border-color: var(--primary-200);
  box-shadow: 0 0 0 4px rgba(253, 87, 50, 0.1);
}

.image-options {
  margin-top: 1rem;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  font-size: 0.95rem;
  color: var(--text-100);
}

.checkbox-label input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.process-actions {
  text-align: center;
  margin: 2rem 0;
}

.btn-lg {
  padding: 1rem 2.5rem;
  font-size: 1.05rem;
}

.spinner {
  display: inline-block;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.results-section {
  margin-top: 2rem;
  padding-top: 2rem;
  border-top: 2px solid var(--border-color);
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.results-actions {
  display: flex;
  gap: 0.5rem;
}

.btn-icon {
  padding: 0.5rem;
  background: transparent;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 1.2rem;
}

.btn-icon:hover {
  background: var(--bg-100);
  border-color: var(--primary-200);
  transform: scale(1.1);
}

.result-box {
  padding: 1.5rem;
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.05), rgba(52, 211, 153, 0.05));
  border: 2px solid rgba(16, 185, 129, 0.2);
  border-radius: 12px;
  margin-bottom: 1rem;
}

.result-content {
  color: var(--text-100);
  line-height: 1.8;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.result-meta {
  display: flex;
  gap: 2rem;
  flex-wrap: wrap;
}

.meta-item {
  display: flex;
  gap: 0.5rem;
}

.meta-label {
  font-weight: 600;
  color: var(--text-200);
  font-size: 0.875rem;
}

.meta-value {
  color: var(--text-100);
  font-size: 0.875rem;
}

@keyframes fadeIn {
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
