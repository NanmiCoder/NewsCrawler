// 类型定义
export interface NewsMetaInfo {
  author_name: string
  author_url: string
  publish_time: string
}

export interface ContentItem {
  type: 'text' | 'image' | 'video'
  content: string
  desc: string
}

export interface NewsItem {
  title: string
  news_url: string
  news_id: string
  meta_info: NewsMetaInfo
  contents: ContentItem[]
  texts: string[]
  images: string[]
  videos: string[]
}

export interface ExtractRequest {
  url: string
  output_format: 'json' | 'markdown'
  platform?: string
}

export interface ExtractResponse {
  status: string
  data?: NewsItem
  markdown?: string
  platform?: string
  extracted_at: string
  error?: {
    code: string
    message: string
  }
}

export interface Platform {
  id: string
  name: string
  icon: string
}

// AI Agent types
export type LLMProvider = 'openai' | 'anthropic' | 'gemini' | 'deepseek' | 'qwen' | 'kimi'
export type AgentTaskType = 'summarize' | 'rewrite' | 'translate' | 'extract_keywords'

export interface LLMConfig {
  provider: LLMProvider
  model_name: string
  api_key: string
  base_url?: string
  temperature?: number
  max_tokens?: number
}

export interface AgentRequest {
  llm_config: LLMConfig
  task_type: AgentTaskType
  content: string
  images?: string[]
  custom_prompt?: string
}

export interface AgentResponse {
  status: string
  result?: string
  original_content: string
  task_type: string
  provider: string
  model: string
  error?: {
    code: string
    message: string
  }
}

export interface LLMProviderInfo {
  id: string
  name: string
  default_model: string
  supports_vision: boolean
}

export interface TaskInfo {
  id: string
  name: string
  description: string
  icon: string
}
