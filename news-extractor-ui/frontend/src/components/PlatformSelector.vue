<template>
  <div class="platform-selector">
    <div class="section-header">
      <h2 class="section-title">
        <span class="title-icon">🚀</span>
        <span>{{ t('platforms.selectTitle') }}</span>
      </h2>
      <p class="section-desc">{{ t('platforms.selectDesc') }}</p>
    </div>

    <div class="platforms-grid">
      <div
        v-for="platform in platforms"
        :key="platform.id"
        class="platform-card"
        :class="{ active: selectedPlatform === platform.id }"
        @click="selectPlatform(platform.id)"
      >
        <div class="card-glow"></div>
        <div class="platform-icon">
          <img :src="platform.icon" :alt="platform.name" class="platform-logo" />
        </div>
        <div class="platform-info">
          <h3 class="platform-name">{{ platform.name }}</h3>
          <p class="platform-desc">{{ platform.description }}</p>
        </div>
        <div class="platform-badge" v-if="selectedPlatform === platform.id">
          <span class="badge-check">✓</span>
        </div>
        <div class="card-shine"></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'

interface Platform {
  id: string
  name: string
  icon: string
  description: string
}

const { t } = useI18n()

const emit = defineEmits<{
  'platform-selected': [platformId: string]
}>()

const selectedPlatform = ref<string>('')

const platforms = computed<Platform[]>(() => [
  {
    id: 'wechat',
    name: t('platforms.wechat.name'),
    icon: '/logos/wechat.webp',
    description: t('platforms.wechat.description')
  },
  {
    id: 'toutiao',
    name: t('platforms.toutiao.name'),
    icon: '/logos/toutiao.png',
    description: t('platforms.toutiao.description')
  },
  {
    id: 'netease',
    name: t('platforms.netease.name'),
    icon: '/logos/wangyi.webp',
    description: t('platforms.netease.description')
  },
  {
    id: 'sohu',
    name: t('platforms.sohu.name'),
    icon: '/logos/sohu.jpg',
    description: t('platforms.sohu.description')
  },
  {
    id: 'tencent',
    name: t('platforms.tencent.name'),
    icon: '/logos/tencent_news.webp',
    description: t('platforms.tencent.description')
  },
  {
    id: 'lenny',
    name: t('platforms.lenny.name'),
    icon: '/logos/lennys_newsletter_logo.jpeg',
    description: t('platforms.lenny.description')
  },
  {
    id: 'naver',
    name: t('platforms.naver.name'),
    icon: '/logos/Naver_Blog.jpg',
    description: t('platforms.naver.description')
  },
  {
    id: 'detik',
    name: t('platforms.detik.name'),
    icon: '/logos/Detik_News.png',
    description: t('platforms.detik.description')
  },
  {
    id: 'quora',
    name: t('platforms.quora.name'),
    icon: '/logos/Quora.png',
    description: t('platforms.quora.description')
  },
  {
    id: 'bbc',
    name: t('platforms.bbc.name'),
    icon: '/logos/bbc.png',
    description: t('platforms.bbc.description')
  },
  {
    id: 'cnn',
    name: t('platforms.cnn.name'),
    icon: '/logos/cnn.png',
    description: t('platforms.cnn.description')
  }
])

const selectPlatform = (platformId: string) => {
  selectedPlatform.value = platformId
  emit('platform-selected', platformId)
}
</script>

<style scoped>
.platform-selector {
  margin-bottom: 2.5rem;
  animation: fadeIn 0.6s ease-out 0.2s both;
}

.section-header {
  text-align: center;
  margin-bottom: 2.5rem;
}

.section-title {
  font-size: 2rem;
  font-weight: 800;
  margin-bottom: 0.75rem;
  color: var(--text-100);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
}

.title-icon {
  font-size: 2rem;
  filter: drop-shadow(0 4px 8px rgba(253, 87, 50, 0.3));
}

.section-desc {
  color: var(--text-200);
  font-size: 1.05rem;
  max-width: 500px;
  margin: 0 auto;
  line-height: 1.6;
}

.platforms-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
}

.platform-card {
  position: relative;
  padding: 2rem;
  border: 2px solid rgba(194, 29, 3, 0.1);
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  background: white;
  display: flex;
  align-items: flex-start;
  gap: 1.25rem;
  overflow: hidden;
}

.platform-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, var(--primary-200), var(--primary-300));
  transform: scaleX(0);
  transform-origin: left;
  transition: transform 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.platform-card:hover::before {
  transform: scaleX(1);
}

.card-glow {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  background: radial-gradient(circle, rgba(253, 87, 50, 0.15), transparent 70%);
  border-radius: 50%;
  transform: translate(-50%, -50%);
  transition: all 0.6s cubic-bezier(0.4, 0, 0.2, 1);
  pointer-events: none;
}

.platform-card:hover .card-glow {
  width: 300px;
  height: 300px;
}

.card-shine {
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
  transition: left 0.6s;
  pointer-events: none;
}

.platform-card:hover .card-shine {
  left: 100%;
}

.platform-card:hover {
  border-color: var(--primary-200);
  transform: translateY(-4px);
  box-shadow: 0 12px 40px rgba(253, 87, 50, 0.2);
}

.platform-card.active {
  border-color: var(--primary-200);
  background: linear-gradient(135deg, rgba(253, 87, 50, 0.03), rgba(255, 183, 135, 0.05));
  box-shadow: 0 8px 32px rgba(253, 87, 50, 0.25);
  transform: translateY(-2px);
}

.platform-card.active::before {
  transform: scaleX(1);
}

.platform-icon {
  width: 64px;
  height: 64px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.platform-logo {
  width: 100%;
  height: 100%;
  object-fit: contain;
  filter: drop-shadow(0 2px 8px rgba(0, 0, 0, 0.1));
  transition: filter 0.3s;
}

.platform-card:hover .platform-icon {
  transform: scale(1.1);
}

.platform-card:hover .platform-logo {
  filter: drop-shadow(0 4px 12px rgba(253, 87, 50, 0.3));
}

.platform-card.active .platform-logo {
  filter: drop-shadow(0 4px 12px rgba(253, 87, 50, 0.4));
}

.platform-info {
  flex: 1;
}

.platform-name {
  font-size: 1.15rem;
  font-weight: 700;
  margin-bottom: 0.4rem;
  color: var(--text-100);
  transition: color 0.3s;
}

.platform-card:hover .platform-name {
  color: var(--primary-100);
}

.platform-desc {
  font-size: 0.9rem;
  color: var(--text-200);
  margin: 0;
  line-height: 1.5;
}

.platform-badge {
  position: absolute;
  top: 1rem;
  right: 1rem;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--primary-200), var(--primary-100));
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(253, 87, 50, 0.4);
  animation: bounceIn 0.5s cubic-bezier(0.68, -0.55, 0.265, 1.55);
}

.badge-check {
  font-size: 1rem;
  font-weight: bold;
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

@keyframes bounceIn {
  0% {
    transform: scale(0);
    opacity: 0;
  }
  50% {
    transform: scale(1.2);
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
}

@media (max-width: 768px) {
  .platforms-grid {
    grid-template-columns: 1fr;
    gap: 1rem;
  }

  .platform-card {
    padding: 1.5rem;
  }

  .section-title {
    font-size: 1.5rem;
  }
}
</style>
