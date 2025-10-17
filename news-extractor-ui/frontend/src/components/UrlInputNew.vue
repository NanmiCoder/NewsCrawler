<template>
  <div class="url-input-new card">
    <div class="section-header">
      <h2 class="section-title">
        <span class="title-icon">🔗</span>
        <span>{{ t('input.title') }}</span>
      </h2>
    </div>

    <div class="input-container">
      <div class="input-wrapper">
        <div class="input-icon">🌐</div>
        <input
          ref="urlInput"
          v-model="url"
          type="text"
          class="input url-input"
          :placeholder="placeholder"
          @keyup.enter="handleExtract"
          @paste="handlePaste"
        />
        <button
          v-if="url"
          class="btn-clear"
          @click="clearInput"
          :title="t('input.clear')"
        >
          <span class="clear-icon">✕</span>
        </button>
      </div>

      <transition name="slide-down">
        <div class="platform-detected" v-if="detectedPlatform && url">
          <div class="detected-content">
            <span class="detected-icon">✓</span>
            <span class="detected-text">
              {{ t('input.detectedPlatform') }}: <strong class="platform-highlight">{{ platformName }}</strong>
            </span>
          </div>
          <div class="detected-badge">{{ t('input.smartDetection') }}</div>
        </div>
      </transition>
    </div>

    <div class="action-bar">
      <button
        class="btn btn-primary extract-btn"
        @click="handleExtract"
        :disabled="!url || loading"
      >
        <span v-if="loading" class="loading-spinner">⏳</span>
        <span v-else class="btn-icon">🚀</span>
        <span class="btn-text">{{ loading ? t('input.extracting') : t('input.extractButton') }}</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const props = defineProps<{
  loading: boolean
  selectedPlatform?: string
}>()

const emit = defineEmits<{
  extract: [url: string]
}>()

const url = ref('')
const urlInput = ref<HTMLInputElement>()
const detectedPlatform = ref('')

const platformMap: Record<string, string> = {
  'mp.weixin.qq.com': 'wechat',
  'toutiao.com': 'toutiao',
  '163.com': 'netease',
  'sohu.com': 'sohu',
  'news.qq.com': 'tencent',
  'detik.com': 'detik',
  'naver.com': 'naver',
  'lennysnewsletter.com': 'lenny',
  'quora.com': 'quora'
}

const platformName = computed(() => {
  if (!detectedPlatform.value) return ''
  const key = platformMap[detectedPlatform.value]
  return key ? t(`platforms.${key}.name`) : ''
})

// 每个平台的示例 placeholder
const platformPlaceholders = computed(() => ({
  'wechat': t('input.placeholders.wechat'),
  'toutiao': t('input.placeholders.toutiao'),
  'netease': t('input.placeholders.netease'),
  'sohu': t('input.placeholders.sohu'),
  'tencent': t('input.placeholders.tencent'),
  'lenny': t('input.placeholders.lenny'),
  'naver': t('input.placeholders.naver'),
  'detik': t('input.placeholders.detik'),
  'quora': t('input.placeholders.quora')
}))

const placeholder = ref(t('input.placeholders.default'))

// 监听 URL 变化，自动检测平台
watch(url, (newUrl) => {
  if (!newUrl) {
    detectedPlatform.value = ''
    return
  }

  for (const domain of Object.keys(platformMap)) {
    if (newUrl.includes(domain)) {
      detectedPlatform.value = domain
      return
    }
  }

  detectedPlatform.value = ''
})

// 监听选中的平台，更新 placeholder
watch(() => props.selectedPlatform, (newPlatform) => {
  if (newPlatform && platformPlaceholders.value[newPlatform]) {
    placeholder.value = platformPlaceholders.value[newPlatform]
  } else {
    placeholder.value = t('input.placeholders.default')
  }
})

const handlePaste = (event: ClipboardEvent) => {
  // 自动检测粘贴的内容
  setTimeout(() => {
    if (url.value && detectedPlatform.value) {
      // 可以添加提示音效或动画
    }
  }, 100)
}

const clearInput = () => {
  url.value = ''
  urlInput.value?.focus()
}

const handleExtract = () => {
  if (!url.value || props.loading) return
  emit('extract', url.value)
}
</script>

<style scoped>
.url-input-new {
  animation: fadeIn 0.6s ease-out 0.4s both;
}

.section-header {
  text-align: center;
  margin-bottom: 2rem;
}

.section-title {
  font-size: 1.75rem;
  font-weight: 800;
  color: var(--text-100);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
}

.title-icon {
  font-size: 1.75rem;
  filter: drop-shadow(0 2px 6px rgba(253, 87, 50, 0.3));
}

.input-container {
  margin-bottom: 2rem;
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
}

.input-icon {
  position: absolute;
  left: 1.25rem;
  font-size: 1.25rem;
  z-index: 1;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.1));
}

.url-input {
  width: 100%;
  padding-left: 3.5rem;
  padding-right: 4rem;
  font-size: 1rem;
  font-weight: 500;
  border: 2px solid var(--bg-200);
  background: var(--bg-100);
}

.url-input:focus {
  border-color: var(--primary-200);
  background: white;
}

.btn-clear {
  position: absolute;
  right: 1rem;
  top: 50%;
  transform: translateY(-50%);
  width: 36px;
  height: 36px;
  border: none;
  background: linear-gradient(135deg, rgba(194, 29, 3, 0.1), rgba(253, 87, 50, 0.1));
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 1;
}

.clear-icon {
  font-size: 1.1rem;
  color: var(--text-200);
  transition: all 0.3s;
}

.btn-clear:hover {
  background: linear-gradient(135deg, var(--primary-200), var(--primary-100));
  transform: translateY(-50%) scale(1.1);
}

.btn-clear:hover .clear-icon {
  color: white;
}

.platform-detected {
  padding: 1rem 1.5rem;
  background: linear-gradient(135deg, rgba(253, 87, 50, 0.08), rgba(255, 183, 135, 0.05));
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border: 2px solid rgba(253, 87, 50, 0.2);
  box-shadow: 0 4px 12px rgba(253, 87, 50, 0.1);
}

.detected-content {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.detected-icon {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--primary-200), var(--primary-100));
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.95rem;
  font-weight: bold;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(253, 87, 50, 0.3);
}

.detected-text {
  color: var(--text-100);
  font-size: 1rem;
  font-weight: 500;
}

.platform-highlight {
  color: var(--primary-100);
  font-weight: 700;
}

.detected-badge {
  padding: 0.375rem 0.875rem;
  background: linear-gradient(135deg, var(--primary-200), var(--primary-100));
  color: white;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 700;
  letter-spacing: 0.5px;
  box-shadow: 0 2px 8px rgba(253, 87, 50, 0.3);
}

.action-bar {
  display: flex;
  justify-content: center;
  align-items: center;
}

.extract-btn {
  padding: 1rem 3rem;
  font-size: 1.1rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-weight: 700;
  min-width: 200px;
  justify-content: center;
}

.btn-icon {
  font-size: 1.25rem;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2));
}

.extract-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none !important;
}

.loading-spinner {
  animation: spin 1s linear infinite;
  font-size: 1.25rem;
}

/* Transitions */
.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.slide-down-enter-from {
  opacity: 0;
  transform: translateY(-10px);
  max-height: 0;
}

.slide-down-enter-to {
  opacity: 1;
  transform: translateY(0);
  max-height: 100px;
}

.slide-down-leave-from {
  opacity: 1;
  transform: translateY(0);
  max-height: 100px;
}

.slide-down-leave-to {
  opacity: 0;
  transform: translateY(-10px);
  max-height: 0;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 768px) {
  .section-title {
    font-size: 1.5rem;
  }

  .extract-btn {
    padding: 0.875rem 2rem;
    font-size: 1rem;
    min-width: 160px;
  }

  .platform-detected {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.75rem;
  }

  .detected-badge {
    align-self: flex-end;
  }
}
</style>
