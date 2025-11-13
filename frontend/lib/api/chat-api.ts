// lib/api/chat-api.ts
import { ChatHistoryResponse, Message } from '@/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL;

export async function fetchChatHistory(
  userId: string,
  limit: number = 50
): Promise<Message[]> {
  const response = await fetch(
    `${API_URL}/messages/${userId}?limit=${limit}`
  );

  if (!response.ok) {
    throw new Error(`Failed to fetch chat history: ${response.status}`);
  }

  const data: ChatHistoryResponse = await response.json();
  return data.messages;
}
