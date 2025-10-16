<template>
  <div class="language-switcher">
    <button
      @click="switchLanguage"
      class="lang-button"
      :title="currentLang === 'zh-CN' ? 'Switch to English' : '切换到中文'"
    >
      <svg
        class="lang-icon"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
      >
        <circle cx="12" cy="12" r="10"/>
        <path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
      </svg>
      <span class="lang-text">{{ currentLang === 'zh-CN' ? 'EN' : '中文' }}</span>
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useLanguageStore } from '../stores/language'

const { locale } = useI18n()
const languageStore = useLanguageStore()

const currentLang = computed(() => languageStore.currentLanguage)

const switchLanguage = () => {
  const newLang = currentLang.value === 'zh-CN' ? 'en' : 'zh-CN'
  languageStore.setLanguage(newLang)
  locale.value = newLang
}
</script>

<style scoped>
.language-switcher {
  display: inline-flex;
  align-items: center;
}

.lang-button {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: linear-gradient(135deg, #FD5732, #FFB787);
  border: none;
  border-radius: 8px;
  color: white;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(253, 87, 50, 0.3);
}

.lang-button:hover {
  background: linear-gradient(135deg, #E54622, #FF9F6F);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(253, 87, 50, 0.4);
}

.lang-icon {
  width: 18px;
  height: 18px;
}

.lang-text {
  min-width: 24px;
  text-align: center;
}
</style>
