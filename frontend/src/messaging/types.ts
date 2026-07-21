export type EntityId = string;
export type IsoDateTime = string;

export type UserPresence = "online" | "away" | "offline" | "unknown";
export type UserAccountStatus = "active" | "blocked" | "disabled";

export interface User {
  id: EntityId;
  displayName: string;
  avatarUrl?: string;
  presence: UserPresence;
  accountStatus: UserAccountStatus;
}

export type ConversationType = "direct" | "group";
export type ConversationMemberRole = "owner" | "admin" | "member";
export type ConversationMemberStatus = "joined" | "invited" | "left";

export interface ConversationMember {
  user: User;
  role: ConversationMemberRole;
  status: ConversationMemberStatus;
  joinedAt?: IsoDateTime;
}

export interface ConversationPermissions {
  canSendMessages: boolean;
  canEditOwnMessages: boolean;
  canDeleteOwnMessages: boolean;
  canUploadAttachments: boolean;
  canInviteMembers: boolean;
  canChangeDetails: boolean;
}

export interface Conversation {
  id: EntityId;
  type: ConversationType;
  title: string;
  avatarUrl?: string;
  members: ConversationMember[];
  lastMessage?: MessagePreview;
  unreadCount: number;
  isMuted: boolean;
  isArchived: boolean;
  permissions: ConversationPermissions;
  createdAt: IsoDateTime;
  updatedAt: IsoDateTime;
}

export interface MessagePreview {
  id: EntityId;
  conversationId: EntityId;
  senderId: EntityId;
  senderName: string;
  text: string;
  createdAt: IsoDateTime;
}

export type AttachmentType = "image" | "document";

export interface Attachment {
  id: EntityId;
  type: AttachmentType;
  name: string;
  mimeType: string;
  size: number;
  url?: string;
  thumbnailUrl?: string;
}

export type MessageStatus =
  | "queued"
  | "sending"
  | "sent"
  | "delivered"
  | "read"
  | "failed";

export interface Message {
  id: EntityId;
  conversationId: EntityId;
  sender: User;
  body: string;
  attachments: Attachment[];
  replyToMessageId?: EntityId;
  clientMessageId?: EntityId;
  createdAt: IsoDateTime;
  editedAt?: IsoDateTime;
  deletedAt?: IsoDateTime;
  status: MessageStatus;
  isOwn: boolean;
}

export interface MessagePage {
  messages: Message[];
  nextCursor?: string;
  hasMore: boolean;
}

export interface ReadReceipt {
  conversationId: EntityId;
  messageId: EntityId;
  userId: EntityId;
  readAt: IsoDateTime;
}

export interface TypingState {
  conversationId: EntityId;
  userIds: EntityId[];
  updatedAt: IsoDateTime;
}

export type ConnectionState =
  | "idle"
  | "connecting"
  | "connected"
  | "reconnecting"
  | "offline"
  | "failed";

export type MessagingErrorCode =
  | "unauthenticated"
  | "forbidden"
  | "not_found"
  | "rate_limited"
  | "offline"
  | "unknown";

export interface MessagingError {
  code: MessagingErrorCode;
  message: string;
  requestId?: string;
  retryable: boolean;
}

export type MessagingEvent =
  | { type: "connection.changed"; state: ConnectionState }
  | { type: "message.created"; message: Message }
  | { type: "message.updated"; message: Message }
  | {
      type: "message.deleted";
      conversationId: EntityId;
      messageId: EntityId;
      deletedAt: IsoDateTime;
    }
  | { type: "conversation.created"; conversation: Conversation }
  | { type: "conversation.updated"; conversation: Conversation }
  | { type: "conversation.removed"; conversationId: EntityId }
  | { type: "typing.changed"; typing: TypingState }
  | { type: "presence.changed"; user: User }
  | { type: "receipt.updated"; receipt: ReadReceipt }
  | { type: "error"; error: MessagingError };
