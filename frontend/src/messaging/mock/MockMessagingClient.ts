import type {
  CreateConversationInput,
  DeleteMessageInput,
  EditMessageInput,
  GetMessagesOptions,
  ListConversationsOptions,
  MessagingClient,
  MessagingEventHandler,
  SendMessageInput,
  Unsubscribe,
  UploadAttachmentInput,
} from "../MessagingClient";
import type { Attachment, Conversation, EntityId, Message, MessagePage, User } from "../types";
import { mockConversations, mockCurrentUser, mockMessagesByConversation, mockUsers } from "./fixtures";

export interface MockMessagingSeed {
  me: User;
  users: User[];
  conversations: Conversation[];
  messagesByConversation: Record<EntityId, Message[]>;
}

export class MockMessagingClient implements MessagingClient {
  private me: User;
  private users: User[];
  private conversations: Conversation[];
  private messagesByConversation: Record<EntityId, Message[]>;
  private handlers = new Set<MessagingEventHandler>();

  constructor(seed?: Partial<MockMessagingSeed>) {
    this.me = seed?.me ?? mockCurrentUser;
    this.users = [...(seed?.users ?? mockUsers)];
    this.conversations = clone(seed?.conversations ?? mockConversations);
    this.messagesByConversation = clone(seed?.messagesByConversation ?? mockMessagesByConversation);
  }

  async start(): Promise<void> {
    this.emit({ type: "connection.changed", state: "connected" });
  }

  async stop(): Promise<void> {
    this.emit({ type: "connection.changed", state: "offline" });
  }

  async getMe(): Promise<User> {
    return this.me;
  }

  async listConversations(options: ListConversationsOptions = {}): Promise<Conversation[]> {
    const query = options.query?.trim().toLowerCase();
    const limit = options.limit ?? this.conversations.length;
    const conversations = query
      ? this.conversations.filter((conversation) => conversation.title.toLowerCase().includes(query))
      : this.conversations;

    return conversations
      .slice(0, limit)
      .sort((left, right) => right.updatedAt.localeCompare(left.updatedAt));
  }

  async getConversation(conversationId: EntityId): Promise<Conversation> {
    return this.requireConversation(conversationId);
  }

  async getMessages({ conversationId, cursor, limit = 30 }: GetMessagesOptions): Promise<MessagePage> {
    const messages = this.messagesByConversation[conversationId] ?? [];
    const end = cursor ? Number.parseInt(cursor, 10) : messages.length;
    const safeEnd = Number.isNaN(end) ? messages.length : end;
    const start = Math.max(0, safeEnd - limit);

    return {
      messages: messages.slice(start, safeEnd),
      nextCursor: start > 0 ? String(start) : undefined,
      hasMore: start > 0,
    };
  }

  async createConversation(input: CreateConversationInput): Promise<Conversation> {
    const now = new Date().toISOString();
    const members = [this.me.id, ...input.memberIds]
      .filter(unique)
      .map((userId) => this.users.find((user) => user.id === userId))
      .filter((user): user is User => Boolean(user))
      .map((user) => ({
        user,
        role: user.id === this.me.id ? ("owner" as const) : ("member" as const),
        status: "joined" as const,
        joinedAt: now,
      }));

    const conversation: Conversation = {
      id: `conv_${Date.now()}`,
      type: input.type,
      title: input.title ?? members.filter((member) => member.user.id !== this.me.id).map((member) => member.user.displayName).join(", "),
      members,
      unreadCount: 0,
      isMuted: false,
      isArchived: false,
      permissions: {
        canSendMessages: true,
        canEditOwnMessages: true,
        canDeleteOwnMessages: true,
        canUploadAttachments: true,
        canInviteMembers: input.type === "group",
        canChangeDetails: input.type === "group",
      },
      createdAt: now,
      updatedAt: now,
    };

    this.conversations = [conversation, ...this.conversations];
    this.messagesByConversation[conversation.id] = [];
    this.emit({ type: "conversation.created", conversation });

    return conversation;
  }

  async sendMessage(input: SendMessageInput): Promise<Message> {
    const conversation = this.requireConversation(input.conversationId);
    const now = new Date().toISOString();
    const message: Message = {
      id: `msg_${Date.now()}`,
      conversationId: input.conversationId,
      sender: this.me,
      body: input.body,
      attachments: input.attachments ?? [],
      replyToMessageId: input.replyToMessageId,
      clientMessageId: input.clientMessageId,
      createdAt: now,
      status: "sent",
      isOwn: true,
    };

    this.messagesByConversation[input.conversationId] = [
      ...(this.messagesByConversation[input.conversationId] ?? []),
      message,
    ];
    this.updateConversation(conversation.id, {
      updatedAt: now,
      lastMessage: {
        id: message.id,
        conversationId: message.conversationId,
        senderId: this.me.id,
        senderName: this.me.displayName,
        text: message.body,
        createdAt: message.createdAt,
      },
    });
    this.emit({ type: "message.created", message });

    return message;
  }

  async editMessage(input: EditMessageInput): Promise<Message> {
    const message = this.requireMessage(input.messageId);
    const editedMessage: Message = {
      ...message,
      body: input.body,
      editedAt: new Date().toISOString(),
    };

    this.replaceMessage(editedMessage);
    this.emit({ type: "message.updated", message: editedMessage });

    return editedMessage;
  }

  async deleteMessage(input: DeleteMessageInput): Promise<void> {
    const message = this.requireMessage(input.messageId);
    const deletedAt = new Date().toISOString();

    this.replaceMessage({
      ...message,
      body: "",
      attachments: [],
      deletedAt,
    });
    this.emit({
      type: "message.deleted",
      conversationId: input.conversationId,
      messageId: input.messageId,
      deletedAt,
    });
  }

  async uploadAttachment(input: UploadAttachmentInput): Promise<Attachment> {
    const type = input.file.type.startsWith("image/") ? "image" : "document";

    return {
      id: `att_${Date.now()}`,
      type,
      name: input.file.name,
      mimeType: input.file.type || "application/octet-stream",
      size: input.file.size,
      url: input.previewUrl,
      thumbnailUrl: type === "image" ? input.previewUrl : undefined,
    };
  }

  async markAsRead(conversationId: EntityId, messageId: EntityId): Promise<void> {
    const readAt = new Date().toISOString();

    this.updateConversation(conversationId, { unreadCount: 0 });
    this.emit({
      type: "receipt.updated",
      receipt: {
        conversationId,
        messageId,
        userId: this.me.id,
        readAt,
      },
    });
  }

  async setTyping(conversationId: EntityId, isTyping: boolean): Promise<void> {
    this.emit({
      type: "typing.changed",
      typing: {
        conversationId,
        userIds: isTyping ? [this.me.id] : [],
        updatedAt: new Date().toISOString(),
      },
    });
  }

  onEvent(handler: MessagingEventHandler): Unsubscribe {
    this.handlers.add(handler);
    return () => this.handlers.delete(handler);
  }

  private emit(event: Parameters<MessagingEventHandler>[0]): void {
    for (const handler of this.handlers) {
      handler(event);
    }
  }

  private requireConversation(conversationId: EntityId): Conversation {
    const conversation = this.conversations.find((item) => item.id === conversationId);

    if (!conversation) {
      throw new Error(`Conversation not found: ${conversationId}`);
    }

    return conversation;
  }

  private requireMessage(messageId: EntityId): Message {
    for (const messages of Object.values(this.messagesByConversation)) {
      const message = messages.find((item) => item.id === messageId);

      if (message) {
        return message;
      }
    }

    throw new Error(`Message not found: ${messageId}`);
  }

  private replaceMessage(nextMessage: Message): void {
    const messages = this.messagesByConversation[nextMessage.conversationId] ?? [];

    this.messagesByConversation[nextMessage.conversationId] = messages.map((message) =>
      message.id === nextMessage.id ? nextMessage : message,
    );
  }

  private updateConversation(conversationId: EntityId, patch: Partial<Conversation>): void {
    let updatedConversation: Conversation | undefined;

    this.conversations = this.conversations.map((conversation) => {
      if (conversation.id !== conversationId) {
        return conversation;
      }

      updatedConversation = { ...conversation, ...patch };
      return updatedConversation;
    });

    if (updatedConversation) {
      this.emit({ type: "conversation.updated", conversation: updatedConversation });
    }
  }
}

function clone<T>(value: T): T {
  return structuredClone(value);
}

function unique(value: EntityId, index: number, values: EntityId[]): boolean {
  return values.indexOf(value) === index;
}
