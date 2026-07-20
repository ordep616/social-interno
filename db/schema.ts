import { index, integer, primaryKey, sqliteTable, text } from "drizzle-orm/sqlite-core";

export const users = sqliteTable("users", {
  id: text("id").primaryKey(),
  email: text("email").notNull().unique(),
  displayName: text("display_name").notNull(),
  avatarKey: text("avatar_key"),
  role: text("role", { enum: ["user", "admin", "auditor"] }).notNull().default("user"),
  status: text("status", { enum: ["active", "blocked", "invited"] }).notNull().default("active"),
  identityProviderId: text("identity_provider_id"),
  createdAt: integer("created_at", { mode: "timestamp" }).notNull(),
});

export const conversations = sqliteTable("conversations", {
  id: text("id").primaryKey(),
  kind: text("kind", { enum: ["direct", "group", "announcement"] }).notNull(),
  title: text("title"),
  createdBy: text("created_by").notNull().references(() => users.id),
  createdAt: integer("created_at", { mode: "timestamp" }).notNull(),
  archivedAt: integer("archived_at", { mode: "timestamp" }),
});

export const conversationMembers = sqliteTable("conversation_members", {
  conversationId: text("conversation_id").notNull().references(() => conversations.id),
  userId: text("user_id").notNull().references(() => users.id),
  memberRole: text("member_role", { enum: ["member", "moderator", "owner"] }).notNull().default("member"),
  lastReadMessageId: text("last_read_message_id"),
  joinedAt: integer("joined_at", { mode: "timestamp" }).notNull(),
}, (table) => [primaryKey({ columns: [table.conversationId, table.userId] })]);

export const messages = sqliteTable("messages", {
  id: text("id").primaryKey(),
  conversationId: text("conversation_id").notNull().references(() => conversations.id),
  authorId: text("author_id").notNull().references(() => users.id),
  body: text("body").notNull(),
  replyToId: text("reply_to_id"),
  createdAt: integer("created_at", { mode: "timestamp" }).notNull(),
  editedAt: integer("edited_at", { mode: "timestamp" }),
  deletedAt: integer("deleted_at", { mode: "timestamp" }),
}, (table) => [index("messages_conversation_created_idx").on(table.conversationId, table.createdAt)]);

export const attachments = sqliteTable("attachments", {
  id: text("id").primaryKey(),
  messageId: text("message_id").notNull().references(() => messages.id),
  objectKey: text("object_key").notNull(),
  fileName: text("file_name").notNull(),
  mediaType: text("media_type").notNull(),
  sizeBytes: integer("size_bytes").notNull(),
  scanStatus: text("scan_status", { enum: ["pending", "clean", "blocked"] }).notNull().default("pending"),
});

export const auditLogs = sqliteTable("audit_logs", {
  id: text("id").primaryKey(),
  actorId: text("actor_id").references(() => users.id),
  action: text("action").notNull(),
  targetType: text("target_type").notNull(),
  targetId: text("target_id"),
  metadataJson: text("metadata_json"),
  occurredAt: integer("occurred_at", { mode: "timestamp" }).notNull(),
}, (table) => [index("audit_occurred_idx").on(table.occurredAt)]);
