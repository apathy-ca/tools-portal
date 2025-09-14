/**
 * Type definitions for The Symposium
 */

export interface Message {
  id: string;
  role: 'user' | 'sage';
  content: string;
  timestamp: string;
  metadata?: {
    sage_name?: string;
    processed_by?: string;
    [key: string]: any;
  };
}

export interface Sage {
  id: string;
  name: string;
  personality_type: string;
  state: string;
  description: string;
  beliefs?: {
    core_values: string[];
    philosophical_stance: string;
    curiosities: string[];
  };
  communication_style?: string;
}

export interface ConversationRequest {
  message: string;
  sage_name?: string;
  conversation_id?: string;
  model_preference?: string;
}

export interface ConversationResponse {
  conversation_id: string;
  message: string;
  sage_name: string;
  model_used: string;
  processing_time: number;
  timestamp: string;
  metadata?: {
    sage_state: string;
    personality_type: string;
  };
}

export interface HealthStatus {
  status: string;
  services: {
    memory: boolean;
    llm: boolean;
    dask: boolean;
  };
  timestamp: string;
}

export interface ApiResponse<T = any> {
  data?: T;
  error?: string;
  status: number;
}

export interface FileUploadResponse {
  file_id: string;
  filename: string;
  analysis: any;
  status: string;
}

export interface SearchResult {
  conversation_id: string;
  message_id: string;
  content: string;
  context: string;
  score: number;
  timestamp: string;
  sage_name: string;
}

export interface ClusterStatus {
  status: string;
  workers: number;
  tasks: {
    pending: number;
    running: number;
    completed: number;
  };
  memory_usage: string;
  cpu_usage: string;
}

export interface AvailableModels {
  models: string[];
  categorized: {
    ollama: string[];
    openai: string[];
    anthropic: string[];
    google: string[];
    cohere: string[];
    huggingface: string[];
    mock: string[];
  };
  total_count: number;
  providers: {
    ollama_available: boolean;
    openai_available: boolean;
    anthropic_available: boolean;
    google_available: boolean;
    cohere_available: boolean;
    huggingface_available: boolean;
  };
}