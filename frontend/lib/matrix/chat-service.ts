import {
  EventStatus,
  EventType,
  MsgType,
  NotificationCountType,
  type MatrixClient,
  type MatrixEvent,
  type Room,
} from "matrix-js-sdk";

import type {
  ChatMessage,
  Conversation,
  MessageDeliveryStatus,
} from "./types";

export interface ChatService {
  connect(): void;
  disconnect(): void;
  listConversations(): Conversation[];
  listMessages(conversationId: string): ChatMessage[];
  loadEarlierMessages(conversationId: string, limit?: number): Promise<void>;
  sendMessage(conversationId: string, body: string): Promise<void>;
  markAsRead(conversationId: string, eventId: string): Promise<void>;
  setTyping(conversationId: string, typing: boolean): Promise<void>;
}

export class MatrixChatService implements ChatService {
  constructor(private readonly client: MatrixClient) {}

  connect(): void {
    this.client.startClient({ initialSyncLimit: 20 });
  }

  disconnect(): void {
    this.client.stopClient();
  }

  listConversations(): Conversation[] {
    return this.client.getRooms().map(mapRoom);
  }

  listMessages(conversationId: string): ChatMessage[] {
    const room = this.requireRoom(conversationId);
    return room
      .getLiveTimeline()
      .getEvents()
      .filter((event) => event.getType() === EventType.RoomMessage)
      .map((event) => mapMessage(room.roomId, event));
  }

  async loadEarlierMessages(
    conversationId: string,
    limit = 30,
  ): Promise<void> {
    await this.client.scrollback(this.requireRoom(conversationId), limit);
  }

  async sendMessage(conversationId: string, body: string): Promise<void> {
    const normalized = body.trim();
    if (!normalized) return;

    await this.client.sendEvent(conversationId, EventType.RoomMessage, {
      msgtype: MsgType.Text,
      body: normalized,
    });
  }

  async markAsRead(conversationId: string, eventId: string): Promise<void> {
    const event = this.requireRoom(conversationId).findEventById(eventId);
    if (!event) throw new Error("Evento não encontrado na linha do tempo local");
    await this.client.sendReadReceipt(event);
  }

  async setTyping(conversationId: string, typing: boolean): Promise<void> {
    await this.client.sendTyping(conversationId, typing, typing ? 10_000 : 0);
  }

  private requireRoom(conversationId: string): Room {
    const room = this.client.getRoom(conversationId);
    if (!room) throw new Error("Conversa Matrix não encontrada");
    return room;
  }
}

function mapRoom(room: Room): Conversation {
  return {
    id: room.roomId,
    name: room.name || "Conversa sem nome",
    unreadCount: room.getUnreadNotificationCount(NotificationCountType.Total),
  };
}

function mapMessage(conversationId: string, event: MatrixEvent): ChatMessage {
  const content = event.getContent<{ body?: string }>();

  return {
    id: event.getId() ?? event.getTxnId() ?? "evento-pendente",
    conversationId,
    senderId: event.getSender() ?? "usuario-desconhecido",
    body: content.body ?? "",
    sentAt: new Date(event.getTs()).toISOString(),
    status: mapDeliveryStatus(event.status),
  };
}

function mapDeliveryStatus(
  status: EventStatus | null,
): MessageDeliveryStatus {
  if (status === EventStatus.NOT_SENT || status === EventStatus.CANCELLED) {
    return "failed";
  }
  if (status) return "sending";
  return "sent";
}
