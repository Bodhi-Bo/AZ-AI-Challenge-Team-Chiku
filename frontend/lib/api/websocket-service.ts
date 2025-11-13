// lib/api/websocket-service.ts
import { ClientMessage, ServerMessage } from '@/types';

export class WebSocketService {
  private ws: WebSocket | null = null;
  private userId: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private heartbeatInterval: NodeJS.Timeout | null = null;

  constructor(userId: string) {
    this.userId = userId;
  }

  connect(
    onMessage: (data: ServerMessage) => void,
    onOpen?: () => void,
    onClose?: () => void
  ) {
    const url = `${process.env.NEXT_PUBLIC_BACKEND_API_URL}/ws/${this.userId}`;
    console.log('🔌 Connecting to:', url);

    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      console.log('✅ WebSocket connected');
      this.reconnectAttempts = 0;
      this.startHeartbeat();
      onOpen?.();
    };

    this.ws.onmessage = (event) => {
      console.log('📨 Raw message received:', event.data);
      try {
        const data: ServerMessage = JSON.parse(event.data);
        console.log('📨 Parsed message:', data);
        onMessage(data);
      } catch (error) {
        console.error('❌ Failed to parse message:', error);
      }
    };

    this.ws.onclose = () => {
      console.log('🔌 WebSocket disconnected');
      this.stopHeartbeat();
      onClose?.();
      this.attemptReconnect(onMessage, onOpen, onClose);
    };

    this.ws.onerror = (error) => {
      console.error('❌ WebSocket error:', error);
    };
  }

  sendMessage(text: string) {
    if (!this.ws) {
      console.error('❌ WebSocket is null');
      return;
    }

    if (this.ws.readyState !== WebSocket.OPEN) {
      console.error('❌ WebSocket not open, state:', this.ws.readyState);
      return;
    }

    const message: ClientMessage = { type: 'message', text };
    const messageStr = JSON.stringify(message);

    console.log('📤 Sending to server:', messageStr);
    this.ws.send(messageStr);
    console.log('✅ Message sent');
  }

  private startHeartbeat() {
    this.heartbeatInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        const ping: ClientMessage = { type: 'ping' };
        this.ws.send(JSON.stringify(ping));
      }
    }, 30000); // Every 30 seconds
  }

  private stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  private attemptReconnect(
    onMessage: (data: ServerMessage) => void,
    onOpen?: () => void,
    onClose?: () => void
  ) {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(
        `🔄 Reconnecting... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`
      );
      setTimeout(() => {
        this.connect(onMessage, onOpen, onClose);
      }, 2000);
    } else {
      console.error('❌ Max reconnection attempts reached');
    }
  }

  disconnect() {
    this.stopHeartbeat();
    this.ws?.close();
  }
}
