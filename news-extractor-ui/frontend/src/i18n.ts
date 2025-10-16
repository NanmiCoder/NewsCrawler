import { createI18n } from 'vue-i18n'
import en from './locales/en.json'
import zhCN from './locales/zh-CN.json'

// Get browser language or default to Chinese
const getBrowserLanguage = (): string => {
  const savedLang = localStorage.getItem('language')
  if (savedLang) {
    return savedLang
  }

  const browserLang = navigator.language.toLowerCase()
  if (browserLang.startsWith('en')) {
    return 'en'
  }
  return 'zh-CN'
}

const i18n = createI18n({
  legacy: false, // Use Composition API mode
  locale: getBrowserLanguage(),
  fallbackLocale: 'zh-CN',
  messages: {
    en,
    'zh-CN': zhCN
  }
})

export default i18n
