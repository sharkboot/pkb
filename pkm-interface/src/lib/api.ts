const API_BASE_URL = 'http://localhost:8000/api/v1';

interface BaseResponse<T = any> {
  code: number;
  message: string;
  data: T;
}

interface Knowledge {
  id: string;
  title: string;
  summary?: string;
  content: string;
  source_refs?: string[];
  tags?: string[];
  relations?: string[];
  status: 'draft' | 'active' | 'archived' | 'deleted';
  category?: string;
  source?: string;
  score: number;
  created_at: string;
  updated_at: string;
}

interface KnowledgeListResponse {
  list: Knowledge[];
  total: number;
  page: number;
  pageSize: number;
}

interface ContentCollectRequest {
  sourceType: 'screenshot' | 'text' | 'web' | 'pdf' | 'image' | 'manual' | 'agent';
  content?: string;
  images?: string[];
  attachments?: string[];
  metadata?: Record<string, any>;
}

async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const defaultHeaders: HeadersInit = {
    'Content-Type': 'application/json',
  };

  const response = await fetch(url, {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  });

  const result: BaseResponse<T> = await response.json();

  if (result.code !== 0) {
    throw new Error(result.message || 'API Error');
  }

  return result.data;
}

// 内容收集 - 存储笔记
export async function collectContent(
  content: string,
  images: string[],
  sourceType: 'screenshot' | 'text' | 'image' = 'text'
): Promise<Knowledge> {
  const request: ContentCollectRequest = {
    sourceType: sourceType,
    content: content,
    images: images.length > 0 ? images : undefined,
  };

  return fetchApi<Knowledge>('/content/collect', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

// 知识库列表
export async function listKnowledge(params: {
  category?: string;
  keyword?: string;
  page?: number;
  pageSize?: number;
} = {}): Promise<KnowledgeListResponse> {
  const searchParams = new URLSearchParams();
  if (params.category) searchParams.set('category', params.category);
  if (params.keyword) searchParams.set('keyword', params.keyword);
  if (params.page) searchParams.set('page', String(params.page));
  if (params.pageSize) searchParams.set('page_size', String(params.pageSize));

  const query = searchParams.toString();
  return fetchApi<KnowledgeListResponse>(`/knowledge${query ? `?${query}` : ''}`);
}

// 获取单个知识
export async function getKnowledge(id: string): Promise<Knowledge> {
  return fetchApi<Knowledge>(`/knowledge/${id}`);
}

// 更新知识
export async function updateKnowledge(
  id: string,
  data: Partial<Knowledge>
): Promise<Knowledge> {
  return fetchApi<Knowledge>(`/knowledge/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

// 删除知识
export async function deleteKnowledge(id: string): Promise<{ success: boolean }> {
  return fetchApi<{ success: boolean }>(`/knowledge/${id}`, {
    method: 'DELETE',
  });
}

// 收藏知识
export async function starKnowledge(id: string): Promise<Knowledge> {
  return fetchApi<Knowledge>(`/knowledge/${id}/star`, {
    method: 'POST',
  });
}

// 恢复删除的知识
export async function restoreKnowledge(id: string): Promise<Knowledge> {
  return fetchApi<Knowledge>(`/knowledge/${id}/restore`, {
    method: 'POST',
  });
}

// 上传图片
export async function uploadImage(
  file: File,
  folder?: string
): Promise<{ url: string; filename: string }> {
  const formData = new FormData();
  formData.append('file', file);
  if (folder) formData.append('folder', folder);

  const response = await fetch(`${API_BASE_URL}/upload/image`, {
    method: 'POST',
    body: formData,
  });

  const result: BaseResponse<{ url: string; filename: string }> = await response.json();
  if (result.code !== 0) {
    throw new Error(result.message || 'Upload failed');
  }
  return result.data;
}

// 会话相关
export interface Session {
  id: string;
  title?: string;
  context?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export async function listSessions(): Promise<Session[]> {
  return fetchApi<Session[]>('/sessions');
}

export async function createSession(title?: string): Promise<Session> {
  return fetchApi<Session>('/sessions', {
    method: 'POST',
    body: JSON.stringify({ title }),
  });
}

export async function deleteSession(id: string): Promise<{ success: boolean }> {
  return fetchApi<{ success: boolean }>(`/sessions/${id}`, {
    method: 'DELETE',
  });
}

// AI 任务相关
export type TaskType = 'ocr' | 'summary' | 'merge' | 'archive' | 'vector_index' | 'deduplication';

export interface Task {
  id: string;
  taskType: TaskType;
  targetId?: string;
  params?: Record<string, any>;
  status: string;
  result?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export async function createTask(
  taskType: TaskType,
  targetId?: string,
  params?: Record<string, any>
): Promise<Task> {
  return fetchApi<Task>('/ai/tasks', {
    method: 'POST',
    body: JSON.stringify({
      taskType,
      targetId,
      params,
    }),
  });
}

export async function getTask(taskId: string): Promise<Task> {
  return fetchApi<Task>(`/ai/tasks/${taskId}`);
}

export async function listTasks(): Promise<Task[]> {
  return fetchApi<Task[]>('/ai/tasks');
}

export { API_BASE_URL };
export type { Knowledge, Session, Task };
