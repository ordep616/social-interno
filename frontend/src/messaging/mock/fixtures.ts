import type { Conversation, ConversationPermissions, Message, User } from "../types";

export const mockCurrentUser: User = {
  id: "user_current",
  displayName: "Voce",
  presence: "online",
  accountStatus: "active",
};

export const mockUsers: User[] = [
  mockCurrentUser,
  {
    id: "user_marina",
    displayName: "Marina Costa",
    presence: "online",
    accountStatus: "active",
  },
  {
    id: "user_rafael",
    displayName: "Rafael Nunes",
    presence: "away",
    accountStatus: "active",
  },
  {
    id: "user_carlos",
    displayName: "Carlos Mendes",
    presence: "offline",
    accountStatus: "active",
  },
];

const defaultPermissions: ConversationPermissions = {
  canSendMessages: true,
  canEditOwnMessages: true,
  canDeleteOwnMessages: true,
  canUploadAttachments: true,
  canInviteMembers: false,
  canChangeDetails: false,
};

export const mockConversations: Conversation[] = [
  {
    id: "conv_product_design",
    type: "group",
    title: "Produto e Design",
    members: [
      { user: mockCurrentUser, role: "member", status: "joined", joinedAt: "2026-07-20T11:00:00Z" },
      { user: mockUsers[1], role: "admin", status: "joined", joinedAt: "2026-07-20T11:00:00Z" },
      { user: mockUsers[2], role: "member", status: "joined", joinedAt: "2026-07-20T11:05:00Z" },
    ],
    lastMessage: {
      id: "msg_004",
      conversationId: "conv_product_design",
      senderId: "user_marina",
      senderName: "Marina Costa",
      text: "Fechamos a pauta de hoje?",
      createdAt: "2026-07-20T13:42:00Z",
    },
    unreadCount: 3,
    isMuted: false,
    isArchived: false,
    permissions: { ...defaultPermissions, canInviteMembers: true, canChangeDetails: true },
    createdAt: "2026-07-20T11:00:00Z",
    updatedAt: "2026-07-20T13:42:00Z",
  },
  {
    id: "conv_carlos",
    type: "direct",
    title: "Carlos Mendes",
    members: [
      { user: mockCurrentUser, role: "member", status: "joined", joinedAt: "2026-07-19T18:00:00Z" },
      { user: mockUsers[3], role: "member", status: "joined", joinedAt: "2026-07-19T18:00:00Z" },
    ],
    lastMessage: {
      id: "msg_102",
      conversationId: "conv_carlos",
      senderId: "user_carlos",
      senderName: "Carlos Mendes",
      text: "O documento ja esta na pasta.",
      createdAt: "2026-07-20T13:31:00Z",
    },
    unreadCount: 0,
    isMuted: false,
    isArchived: false,
    permissions: defaultPermissions,
    createdAt: "2026-07-19T18:00:00Z",
    updatedAt: "2026-07-20T13:31:00Z",
  },
];

export const mockMessagesByConversation: Record<string, Message[]> = {
  conv_product_design: [
    {
      id: "msg_001",
      conversationId: "conv_product_design",
      sender: mockUsers[1],
      body: "Bom dia! Atualizei a proposta com os pontos da reuniao.",
      attachments: [],
      createdAt: "2026-07-20T13:18:00Z",
      status: "read",
      isOwn: false,
    },
    {
      id: "msg_002",
      conversationId: "conv_product_design",
      sender: mockCurrentUser,
      body: "Otimo. Vou revisar a parte de seguranca e acesso corporativo.",
      attachments: [],
      createdAt: "2026-07-20T13:22:00Z",
      status: "read",
      isOwn: true,
    },
    {
      id: "msg_003",
      conversationId: "conv_product_design",
      sender: mockUsers[2],
      body: "Inclui tambem a matriz de componentes para o prototipo.",
      attachments: [],
      createdAt: "2026-07-20T13:29:00Z",
      status: "delivered",
      isOwn: false,
    },
    {
      id: "msg_004",
      conversationId: "conv_product_design",
      sender: mockUsers[1],
      body: "Fechamos a pauta de hoje?",
      attachments: [],
      createdAt: "2026-07-20T13:42:00Z",
      status: "sent",
      isOwn: false,
    },
  ],
  conv_carlos: [
    {
      id: "msg_101",
      conversationId: "conv_carlos",
      sender: mockCurrentUser,
      body: "Pode deixar o documento pronto para revisao?",
      attachments: [],
      createdAt: "2026-07-20T13:10:00Z",
      status: "read",
      isOwn: true,
    },
    {
      id: "msg_102",
      conversationId: "conv_carlos",
      sender: mockUsers[3],
      body: "O documento ja esta na pasta.",
      attachments: [],
      createdAt: "2026-07-20T13:31:00Z",
      status: "read",
      isOwn: false,
    },
  ],
};
