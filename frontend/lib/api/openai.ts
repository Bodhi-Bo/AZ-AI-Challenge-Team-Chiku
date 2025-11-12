// OpenAI API utility - sends to your backend webhook

interface WebhookResponse {
  message?: string;
  openCalendar?: boolean;
  tasks?: Array<{
    id: string;
    title: string;
    startTime: string;
    endTime: string;
    category?: string;
  }>;
  [key: string]: unknown;
}

export async function sendMessage(message: string): Promise<WebhookResponse> {
  try {
    const response = await fetch('/api/webhook', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ message }),
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Failed to send message:', error);
    throw error;
  }
}

export async function streamMessage(
  message: string,
  onChunk: (chunk: string) => void,
  onComplete: (data: WebhookResponse) => void
): Promise<void> {
  try {
    const response = await fetch('/api/webhook', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ message, stream: true }),
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    if (!reader) {
      throw new Error('No response body');
    }

    let fullResponse = '';

    while (true) {
      const { done, value } = await reader.read();

      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      fullResponse += chunk;
      onChunk(chunk);
    }

    // Parse final response
    try {
      const data = JSON.parse(fullResponse);
      onComplete(data);
    } catch {
      onComplete({ message: fullResponse });
    }
  } catch (error) {
    console.error('Failed to stream message:', error);
    throw error;
  }
}
