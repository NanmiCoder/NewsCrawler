<template>
  <div class="ai-config card">
    <div class="config-header">
      <h3 class="config-title">🤖 AI Agent Configuration</h3>
      <button v-if="hasConfig" class="btn-clear" @click="clearConfig">Clear</button>
    </div>

    <!-- Provider Selection -->
    <div class="form-group">
      <label class="form-label">LLM Provider</label>
      <div class="provider-grid">
        <div
          v-for="provider in providers"
          :key="provider.id"
          class="provider-card"
          :class="{ active: config.provider === provider.id }"
          @click="selectProvider(provider)"
        >
          <div class="provider-name">{{ provider.name }}</div>
          <div class="provider-badge" v-if="provider.supports_vision">
            👁️ Vision
          </div>
        </div>
      </div>
    </div>

    <!-- Model Name -->
    <div class="form-group">
      <label class="form-label">Model Name</label>
      <input
        v-model="config.model_name"
        type="text"
        class="input"
        placeholder="e.g., gpt-4o, claude-3-5-sonnet-20241022"
      />
      <div class="form-hint" v-if="selectedProvider">
        Default: {{ selectedProvider.default_model }}
      </div>
    </div>

    <!-- API Key -->
    <div class="form-group">
      <label class="form-label">API Key</label>
      <input
        v-model="config.api_key"
        type="password"
        class="input"
        placeholder="Enter your API key"
      />
    </div>

    <!-- Base URL (Optional) -->
    <div class="form-group">
      <label class="form-label">Base URL (Optional)</label>
      <input
        v-model="config.base_url"
        type="text"
        class="input"
        placeholder="e.g., https://api.openai.com/v1"
      />
      <div class="form-hint">Leave empty to use default URL</div>
    </div>

    <!-- Advanced Settings -->
    <div class="advanced-section">
      <button class="btn-toggle" @click="showAdvanced = !showAdvanced">
        {{ showAdvanced ? '▼' : '▶' }} Advanced Settings
      </button>

      <div v-if="showAdvanced" class="advanced-content">
        <!-- Temperature -->
        <div class="form-group">
          <label class="form-label">Temperature: {{ config.temperature }}</label>
          <input
            v-model.number="config.temperature"
            type="range"
            min="0"
            max="2"
            step="0.1"
            class="slider"
          />
          <div class="slider-labels">
            <span>Precise</span>
            <span>Creative</span>
          </div>
        </div>

        <!-- Max Tokens -->
        <div class="form-group">
          <label class="form-label">Max Tokens</label>
          <input
            v-model.number="config.max_tokens"
            type="number"
            class="input"
            placeholder="2000"
            min="100"
            max="8000"
          />
        </div>
      </div>
    </div>

    <!-- Save Button -->
    <div class="form-actions">
      <button
        class="btn btn-primary"
        :disabled="!isConfigValid"
        @click="saveConfig"
      >
        <span>💾</span>
        <span>Save Configuration</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { getAgentProviders } from '@/services/api'
import type { LLMConfig, LLMProviderInfo, LLMProvider } from '@/types'

const emit = defineEmits<{
  (e: 'config-saved', config: LLMConfig): void
}>()

const providers = ref<LLMProviderInfo[]>([])
const showAdvanced = ref(false)

const config = ref<Partial<LLMConfig> & { provider?: LLMProvider }>({
  provider: undefined,
  model_name: '',
  api_key: '',
  base_url: '',
  temperature: 0.7,
  max_tokens: 2000,
})

const selectedProvider = computed(() => {
  return providers.value.find(p => p.id === config.value.provider)
})

const isConfigValid = computed(() => {
  return !!(
    config.value.provider &&
    config.value.model_name &&
    config.value.api_key
  )
})

const hasConfig = computed(() => {
  return !!(config.value.provider || config.value.model_name || config.value.api_key)
})

const selectProvider = (provider: LLMProviderInfo) => {
  config.value.provider = provider.id as LLMProvider
  if (!config.value.model_name) {
    config.value.model_name = provider.default_model
  }
}

const saveConfig = () => {
  if (isConfigValid.value) {
    const llmConfig: LLMConfig = {
      provider: config.value.provider!,
      model_name: config.value.model_name!,
      api_key: config.value.api_key!,
      base_url: config.value.base_url || undefined,
      temperature: config.value.temperature,
      max_tokens: config.value.max_tokens,
    }
    emit('config-saved', llmConfig)

    // Save to localStorage
    localStorage.setItem('ai_agent_config', JSON.stringify(llmConfig))
  }
}

const clearConfig = () => {
  config.value = {
    provider: undefined,
    model_name: '',
    api_key: '',
    base_url: '',
    temperature: 0.7,
    max_tokens: 2000,
  }
  localStorage.removeItem('ai_agent_config')
}

const loadSavedConfig = () => {
  const saved = localStorage.getItem('ai_agent_config')
  if (saved) {
    try {
      const savedConfig = JSON.parse(saved)
      // Don't load API key from localStorage for security
      config.value = {
        ...savedConfig,
        api_key: '',
      }
    } catch (e) {
      console.error('Failed to load saved config:', e)
    }
  }
}

onMounted(async () => {
  try {
    const response = await getAgentProviders()
    providers.value = response.providers
    loadSavedConfig()
  } catch (error) {
    console.error('Failed to load providers:', error)
  }
})
</script>

<style scoped>
.ai-config {
  animation: fadeIn 0.3s ease-out;
}

.config-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.config-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--text-100);
  margin: 0;
}

.btn-clear {
  padding: 0.5rem 1rem;
  background: transparent;
  border: 1px solid var(--accent-200);
  border-radius: 8px;
  color: var(--text-200);
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-clear:hover {
  background: var(--bg-200);
  border-color: var(--primary-200);
  color: var(--primary-200);
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 600;
  color: var(--text-100);
  font-size: 0.95rem;
}

.form-hint {
  margin-top: 0.5rem;
  font-size: 0.85rem;
  color: var(--text-200);
}

.provider-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 1rem;
}

.provider-card {
  padding: 1rem;
  border: 2px solid var(--border-color);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  text-align: center;
}

.provider-card:hover {
  border-color: var(--primary-200);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(253, 87, 50, 0.15);
}

.provider-card.active {
  border-color: var(--primary-200);
  background: linear-gradient(135deg, rgba(253, 87, 50, 0.1), rgba(255, 183, 135, 0.1));
}

.provider-name {
  font-weight: 600;
  color: var(--text-100);
  margin-bottom: 0.5rem;
}

.provider-badge {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  background: var(--primary-300);
  color: var(--primary-100);
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
}

.advanced-section {
  margin: 2rem 0;
  padding-top: 1.5rem;
  border-top: 2px solid var(--border-color);
}

.btn-toggle {
  padding: 0.75rem 1rem;
  background: transparent;
  border: none;
  color: var(--text-100);
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-toggle:hover {
  color: var(--primary-200);
}

.advanced-content {
  margin-top: 1.5rem;
  animation: slideDown 0.3s ease-out;
}

.slider {
  width: 100%;
  height: 6px;
  border-radius: 3px;
  background: var(--bg-200);
  outline: none;
  -webkit-appearance: none;
}

.slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--primary-200), var(--primary-100));
  cursor: pointer;
  box-shadow: 0 2px 6px rgba(253, 87, 50, 0.3);
}

.slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--primary-200), var(--primary-100));
  cursor: pointer;
  border: none;
  box-shadow: 0 2px 6px rgba(253, 87, 50, 0.3);
}

.slider-labels {
  display: flex;
  justify-content: space-between;
  margin-top: 0.5rem;
  font-size: 0.85rem;
  color: var(--text-200);
}

.form-actions {
  margin-top: 2rem;
  text-align: center;
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

@keyframes slideDown {
  from {
    opacity: 0;
    max-height: 0;
  }
  to {
    opacity: 1;
    max-height: 500px;
  }
}
</style>
