<template>
  <div class="progress-container card">
    <h3 class="progress-title">📊 提取进度</h3>

    <div class="progress-bar-container">
      <div class="progress-bar" :style="{ width: `${progress}%` }"></div>
    </div>

    <div class="progress-info">
      <span class="progress-percentage">{{ progress }}%</span>
      <span class="progress-message">{{ message }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  progress: number
  message: string
}>()
</script>

<style scoped>
.progress-container {
  animation: fadeIn 0.3s ease-out;
}

.progress-title {
  font-size: 1.125rem;
  font-weight: 600;
  margin-bottom: 1rem;
  color: var(--text-primary);
}

.progress-bar-container {
  width: 100%;
  height: 12px;
  background-color: var(--border-color);
  border-radius: 6px;
  overflow: hidden;
  margin-bottom: 0.75rem;
}

.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, var(--primary-color), #60a5fa);
  border-radius: 6px;
  transition: width 0.3s ease-out;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.progress-percentage {
  font-weight: 600;
  color: var(--primary-color);
  font-size: 0.875rem;
}

.progress-message {
  color: var(--text-secondary);
  font-size: 0.875rem;
}
</style>
