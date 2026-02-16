export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface UploadResponse {
  session_id: string;
  dive_count: number;
  dive_numbers: string[];
  message: string;
}

export interface ChatRequest {
  message: string;
  session_id: string;
}
