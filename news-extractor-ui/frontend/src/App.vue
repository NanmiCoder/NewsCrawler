<template>
  <div class="app-container">
    <!-- Hero Section -->
    <header class="hero-section">
      <div class="lang-switcher-wrapper">
        <LanguageSwitcher />
      </div>
      <div class="hero-content">
        <div class="hero-badge-wrapper">
          <div class="hero-badge">
            <span class="badge-icon">✨</span>
            <span>AI-Powered Content Extraction</span>
          </div>
          <span class="coming-soon-tag">{{ t('common.comingSoon') }}</span>
        </div>
        <h1 class="hero-title">
          <span class="title-gradient">{{ t('app.title') }}</span>
        </h1>
        <p class="hero-subtitle">
          {{ t('app.subtitle') }}
        </p>
        <div class="hero-stats">
          <div class="stat-item">
            <span class="stat-number">6+</span>
            <span class="stat-label">{{ t('app.stats.platforms') }}</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <span class="stat-number">99%</span>
            <span class="stat-label">{{ t('app.stats.accuracy') }}</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <span class="stat-number">< 3s</span>
            <span class="stat-label">{{ t('app.stats.responseTime') }}</span>
          </div>
        </div>
      </div>

      <!-- 装饰元素 -->
      <div class="hero-decoration">
        <div class="decoration-circle decoration-1"></div>
        <div class="decoration-circle decoration-2"></div>
        <div class="decoration-circle decoration-3"></div>
      </div>
    </header>

    <main class="app-main">
      <!-- 平台选择器 -->
      <PlatformSelector
        @platform-selected="handlePlatformSelected"
      />

      <!-- URL 输入 -->
      <UrlInputNew
        :loading="loading"
        :selected-platform="selectedPlatform"
        @extract="handleExtract"
      />

      <!-- 提取进度 -->
      <ExtractProgress
        v-if="loading"
        :progress="progress"
        :message="progressMessage"
      />

      <!-- 结果展示 -->
      <ResultViewerNew
        v-if="result && !loading"
        :result="result"
      />

      <!-- 重新开始按钮 -->
      <div v-if="result && !loading" class="restart-section">
        <button class="btn btn-outline" @click="restart">
          <span>🔄</span>
          <span>{{ t('common.extractNew') }}</span>
        </button>
      </div>
    </main>

    <footer class="app-footer">
      <div class="footer-content">
        <div class="footer-brand">
          <img src="/logo.svg" alt="Logo" class="footer-logo" />
          <span class="footer-name">{{ t('app.title') }}</span>
        </div>
        <div class="footer-info">
          <p class="footer-tech">Powered by FastAPI + Vue 3</p>
          <div class="footer-links">
            <a href="https://github.com/NanmiCoder/NewsCrawlerCollection" target="_blank" class="footer-link">
              <span>GitHub</span>
            </a>
            <span class="link-divider">·</span>
            <a href="#" @click.prevent="showAbout" class="footer-link">
              <span>{{ t('common.about') }}</span>
            </a>
          </div>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import PlatformSelector from './components/PlatformSelector.vue'
import UrlInputNew from './components/UrlInputNew.vue'
import ExtractProgress from './components/ExtractProgress.vue'
import ResultViewerNew from './components/ResultViewerNew.vue'
import LanguageSwitcher from './components/LanguageSwitcher.vue'
import { extractNews } from './services/api'
import type { ExtractResponse } from './types'

const { t } = useI18n()

const loading = ref(false)
const progress = ref(0)
const progressMessage = ref('')
const result = ref<ExtractResponse | null>(null)
const selectedPlatform = ref<string>('')

const handlePlatformSelected = (platformId: string) => {
  selectedPlatform.value = platformId
}

const handleExtract = async (url: string) => {
  loading.value = true
  progress.value = 0
  progressMessage.value = t('common.connecting')
  result.value = null

  // 模拟进度
  const progressInterval = setInterval(() => {
    if (progress.value < 90) {
      progress.value += 10
      if (progress.value === 30) progressMessage.value = t('common.fetchingHtml')
      if (progress.value === 60) progressMessage.value = t('common.parsingContent')
      if (progress.value === 90) progressMessage.value = t('common.almostDone')
    }
  }, 500)

  try {
    // 总是请求 markdown 格式，这样所有标签页都能显示
    const response = await extractNews({ url, output_format: 'markdown' })
    progress.value = 100
    progressMessage.value = t('common.extractComplete')

    setTimeout(() => {
      result.value = response
      loading.value = false
      clearInterval(progressInterval)
    }, 500)
  } catch (error: any) {
    clearInterval(progressInterval)
    loading.value = false
    alert(`${t('errors.extractFailed')}: ${error.message}`)
  }
}

const restart = () => {
  result.value = null
  selectedPlatform.value = ''
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

const showAbout = () => {
  const platforms = [
    t('platforms.wechat.name'),
    t('platforms.toutiao.name'),
    t('platforms.lenny.name'),
    t('platforms.naver.name'),
    t('platforms.detik.name'),
    t('platforms.quora.name')
  ].map(p => `- ${p}`).join('\n')

  alert(`${t('app.title')} v2.0\n\n${t('platforms.title')}:\n${platforms}`)
}
</script>

<style scoped>
.app-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1rem 2rem;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  position: relative;
}

/* Hero Section */
.hero-section {
  position: relative;
  padding: 4rem 0 5rem;
  text-align: center;
  overflow: hidden;
}

.lang-switcher-wrapper {
  position: absolute;
  top: 1rem;
  right: 1rem;
  z-index: 10;
}

.hero-content {
  position: relative;
  z-index: 2;
  animation: fadeInUp 0.8s ease-out;
}

.hero-badge-wrapper {
  display: inline-flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1.25rem;
  background: linear-gradient(135deg, rgba(253, 87, 50, 0.1), rgba(255, 183, 135, 0.1));
  border: 1px solid rgba(253, 87, 50, 0.2);
  border-radius: 50px;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--primary-100);
  animation: pulse 2s ease-in-out infinite;
}

.badge-icon {
  font-size: 1.1rem;
}

.coming-soon-tag {
  display: inline-flex;
  align-items: center;
  padding: 0.25rem 0.75rem;
  background: linear-gradient(135deg, #FFB787, #FD5732);
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 700;
  color: white;
  box-shadow: 0 2px 8px rgba(253, 87, 50, 0.3);
  animation: slideInRight 0.6s ease-out 0.3s both;
}

@keyframes slideInRight {
  from {
    opacity: 0;
    transform: translateX(-10px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.hero-title {
  font-size: clamp(2.5rem, 5vw, 4rem);
  font-weight: 900;
  margin-bottom: 1.5rem;
  line-height: 1.2;
}

.title-gradient {
  background: linear-gradient(135deg, var(--primary-100) 0%, var(--primary-200) 50%, var(--primary-300) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  display: inline-block;
  animation: gradientShift 3s ease infinite;
}

.hero-subtitle {
  font-size: clamp(1rem, 2vw, 1.25rem);
  color: var(--text-200);
  max-width: 600px;
  margin: 0 auto 2.5rem;
  line-height: 1.6;
}

.hero-stats {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 2rem;
  flex-wrap: wrap;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
}

.stat-number {
  font-size: 2rem;
  font-weight: 800;
  background: linear-gradient(135deg, var(--primary-200), var(--primary-100));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.stat-label {
  font-size: 0.875rem;
  color: var(--text-200);
  font-weight: 500;
}

.stat-divider {
  width: 1px;
  height: 40px;
  background: linear-gradient(180deg, transparent, var(--accent-200), transparent);
}

/* 装饰元素 */
.hero-decoration {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  overflow: hidden;
  z-index: 1;
}

.decoration-circle {
  position: absolute;
  border-radius: 50%;
  opacity: 0.4;
  filter: blur(60px);
  animation: float 6s ease-in-out infinite;
}

.decoration-1 {
  width: 300px;
  height: 300px;
  background: radial-gradient(circle, var(--primary-300), transparent);
  top: -150px;
  right: 10%;
  animation-delay: 0s;
}

.decoration-2 {
  width: 200px;
  height: 200px;
  background: radial-gradient(circle, var(--primary-200), transparent);
  bottom: -100px;
  left: 5%;
  animation-delay: 2s;
}

.decoration-3 {
  width: 150px;
  height: 150px;
  background: radial-gradient(circle, var(--primary-100), transparent);
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  animation-delay: 4s;
}

.app-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2.5rem;
  position: relative;
  z-index: 2;
}

.restart-section {
  text-align: center;
  padding: 3rem 0;
}

.btn-outline {
  padding: 0.875rem 2.5rem;
  background: white;
  border: 2px solid var(--primary-200);
  color: var(--primary-200);
  font-weight: 600;
  box-shadow: 0 4px 12px rgba(253, 87, 50, 0.15);
}

.btn-outline:hover {
  background: linear-gradient(135deg, var(--primary-200), var(--primary-100));
  border-color: var(--primary-100);
  color: white;
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(253, 87, 50, 0.3);
}

.app-footer {
  margin-top: 4rem;
  padding: 2.5rem 0;
  border-top: 2px solid rgba(194, 29, 3, 0.08);
  position: relative;
  z-index: 2;
}

.footer-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1.5rem;
}

.footer-brand {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.footer-logo {
  width: 36px;
  height: 36px;
  object-fit: contain;
}

.footer-name {
  font-size: 1rem;
  font-weight: 700;
  color: var(--text-100);
}

.footer-info {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.5rem;
}

.footer-tech {
  margin: 0;
  font-size: 0.875rem;
  color: var(--text-200);
}

.footer-links {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.footer-link {
  color: var(--text-200);
  text-decoration: none;
  transition: all 0.3s;
  font-weight: 500;
  font-size: 0.875rem;
  position: relative;
}

.footer-link::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 0;
  width: 0;
  height: 2px;
  background: linear-gradient(90deg, var(--primary-200), var(--primary-100));
  transition: width 0.3s;
}

.footer-link:hover {
  color: var(--primary-200);
}

.footer-link:hover::after {
  width: 100%;
}

.link-divider {
  color: var(--accent-200);
}

/* 动画 */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.8;
    transform: scale(1.02);
  }
}

@keyframes gradientShift {
  0%, 100% {
    background-position: 0% 50%;
  }
  50% {
    background-position: 100% 50%;
  }
}

@keyframes float {
  0%, 100% {
    transform: translateY(0) scale(1);
  }
  50% {
    transform: translateY(-20px) scale(1.1);
  }
}

@media (max-width: 768px) {
  .hero-section {
    padding: 2rem 0 3rem;
  }

  .hero-badge-wrapper {
    flex-direction: column;
    gap: 0.5rem;
  }

  .coming-soon-tag {
    font-size: 0.7rem;
    padding: 0.2rem 0.6rem;
  }

  .hero-stats {
    gap: 1rem;
  }

  .stat-number {
    font-size: 1.5rem;
  }

  .stat-divider {
    height: 30px;
  }

  .footer-content {
    flex-direction: column;
    text-align: center;
  }

  .footer-info {
    align-items: center;
  }

  .decoration-circle {
    display: none;
  }
}
</style>
