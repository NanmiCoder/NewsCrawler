import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useLanguageStore = defineStore('language', () => {
  const currentLanguage = ref<string>(
    localStorage.getItem('language') || 'zh-CN'
  )

  const setLanguage = (lang: string) => {
    currentLanguage.value = lang
    localStorage.setItem('language', lang)
  }

  const toggleLanguage = () => {
    const newLang = currentLanguage.value === 'zh-CN' ? 'en' : 'zh-CN'
    setLanguage(newLang)
  }

  return {
    currentLanguage,
    setLanguage,
    toggleLanguage
  }
})
