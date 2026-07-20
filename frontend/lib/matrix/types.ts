export type MatrixSession = {
  accessToken: string;
  userId: string;
  deviceId?: string;
};

export type Conversation = {
  id: string;
  name: string;
  avatarUrl?: string;
  unreadCount: number;
};

export type MessageDeliveryStatus = "sending" | "sent" | "failed";

export type ChatMessage = {
  id: string;
  conversationId: string;
  senderId: string;
  body: string;
  sentAt: string;
  status: MessageDeliveryStatus;
};
