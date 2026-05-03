/**
 * Roles allowed in the chat system.
 */
export type ChatRole = 'user' | 'assistant';

/**
 * Represents a single message in the chat history.
 */
export interface ChatMessage {
  role: ChatRole;
  content: string;
}

/**
 * Payload for the chat request sent to the backend.
 */
export interface ChatRequestPayload {
  messages: ChatMessage[];
}

/**
 * Successful response from the chat API.
 */
export interface ChatResponse {
  role: 'assistant';
  content: string;
}

/**
 * Error response from the chat API.
 */
export interface ChatErrorResponse {
  error: string;
}
