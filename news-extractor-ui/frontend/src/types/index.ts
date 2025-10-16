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
