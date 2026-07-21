import type {
  Attachment,
  Conversation,
  EntityId,
  Message,
  MessagePage,
  MessagingEvent,
  User,
} from "./types";

export type MessagingEventHandler = (event: MessagingEvent) => void;
export type Unsubscribe = () => void;

export interface ListConversationsOptions {
  query?: string;
  cursor?: string;
  limit?: number;
}

export interface GetMessagesOptions {
  conversationId: EntityId;
  cursor?: string;
  limit?: number;
}

export interface SendMessageInput {
  conversationId: EntityId;
  body: string;
  attachments?: Attachment[];
  replyToMessageId?: EntityId;
  clientMessageId?: EntityId;
}

export interface EditMessageInput {
  messageId: EntityId;
  body: string;
}

export interface DeleteMessageInput {
  conversationId: EntityId;
  messageId: EntityId;
}

export interface UploadAttachmentInput {
  conversationId: EntityId;
  file: File;
  previewUrl?: string;
}

export interface CreateConversationInput {
  type: Conversation["type"];
  title?: string;
  memberIds: EntityId[];
}

export interface MessagingClient {
  start(): Promise<void>;
  stop(): Promise<void>;

  getMe(): Promise<User>;
  listConversations(options?: ListConversationsOptions): Promise<Conversation[]>;
  getConversation(conversationId: EntityId): Promise<Conversation>;
  getMessages(options: GetMessagesOptions): Promise<MessagePage>;

  createConversation(input: CreateConversationInput): Promise<Conversation>;
  sendMessage(input: SendMessageInput): Promise<Message>;
  editMessage(input: EditMessageInput): Promise<Message>;
  deleteMessage(input: DeleteMessageInput): Promise<void>;

  uploadAttachment(input: UploadAttachmentInput): Promise<Attachment>;
  markAsRead(conversationId: EntityId, messageId: EntityId): Promise<void>;
  setTyping(conversationId: EntityId, isTyping: boolean): Promise<void>;

  onEvent(handler: MessagingEventHandler): Unsubscribe;
}
