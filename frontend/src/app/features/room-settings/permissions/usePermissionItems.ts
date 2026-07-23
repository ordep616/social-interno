import { useMemo } from 'react';
import { MessageEvent, StateEvent } from '../../../../types/matrix/room';
import { PermissionGroup } from '../../common-settings/permissions';

export const usePermissionGroups = (): PermissionGroup[] => {
  const groups: PermissionGroup[] = useMemo(() => {
    const messagesGroup: PermissionGroup = {
      name: 'Mensagens',
      items: [
        {
          location: {
            key: MessageEvent.RoomMessage,
          },
          name: 'Enviar mensagens',
        },
        {
          location: {
            key: MessageEvent.Sticker,
          },
          name: 'Enviar figurinhas',
        },
        {
          location: {
            key: MessageEvent.Reaction,
          },
          name: 'Enviar reações',
        },
        {
          location: {
            notification: true,
            key: 'room',
          },
          name: 'Mencionar @room',
        },
        {
          location: {
            state: true,
            key: StateEvent.RoomPinnedEvents,
          },
          name: 'Fixar mensagens',
        },
        {
          location: {},
          name: 'Outros eventos de mensagem',
        },
      ],
    };

    const callSettingsGroup: PermissionGroup = {
      name: 'Chamadas',
      items: [
        {
          location: {
            state: true,
            key: StateEvent.GroupCallMemberPrefix,
          },
          name: 'Iniciar ou entrar em chamada',
        },
      ],
    };

    const moderationGroup: PermissionGroup = {
      name: 'Moderação',
      items: [
        {
          location: {
            action: true,
            key: 'invite',
          },
          name: 'Convidar',
        },
        {
          location: {
            action: true,
            key: 'kick',
          },
          name: 'Remover',
        },
        {
          location: {
            action: true,
            key: 'ban',
          },
          name: 'Banir',
        },
        {
          location: {
            action: true,
            key: 'redact',
          },
          name: 'Excluir mensagens de outras pessoas',
        },
        {
          location: {
            key: MessageEvent.RoomRedaction,
          },
          name: 'Excluir próprias mensagens',
        },
      ],
    };

    const roomOverviewGroup: PermissionGroup = {
      name: 'Visão geral da conversa',
      items: [
        {
          location: {
            state: true,
            key: StateEvent.RoomAvatar,
          },
          name: 'Avatar da conversa',
        },
        {
          location: {
            state: true,
            key: StateEvent.RoomName,
          },
          name: 'Nome da conversa',
        },
        {
          location: {
            state: true,
            key: StateEvent.RoomTopic,
          },
          name: 'Tópico da conversa',
        },
      ],
    };

    const roomSettingsGroup: PermissionGroup = {
      name: 'Configurações',
      items: [
        {
          location: {
            state: true,
            key: StateEvent.RoomJoinRules,
          },
          name: 'Alterar acesso da conversa',
        },
        {
          location: {
            state: true,
            key: StateEvent.RoomCanonicalAlias,
          },
          name: 'Gerenciar endereços',
        },
        {
          location: {
            state: true,
            key: StateEvent.RoomPowerLevels,
          },
          name: 'Alterar todas as permissões',
        },
        {
          location: {
            state: true,
            key: StateEvent.PowerLevelTags,
          },
          name: 'Editar níveis de poder',
        },
        {
          location: {
            state: true,
            key: StateEvent.RoomEncryption,
          },
          name: 'Ativar criptografia',
        },
        {
          location: {
            state: true,
            key: StateEvent.RoomHistoryVisibility,
          },
          name: 'Visibilidade do histórico',
        },
        {
          location: {
            state: true,
            key: StateEvent.RoomTombstone,
          },
          name: 'Atualizar conversa',
        },
        {
          location: {
            state: true,
          },
          name: 'Outras configurações',
        },
      ],
    };

    const otherSettingsGroup: PermissionGroup = {
      name: 'Outros',
      items: [
        {
          location: {
            state: true,
            key: StateEvent.PoniesRoomEmotes,
          },
          name: 'Gerenciar emojis e figurinhas',
        },
        {
          location: {
            state: true,
            key: StateEvent.RoomServerAcl,
          },
          name: 'Alterar ACLs do servidor',
        },
        {
          location: {
            state: true,
            key: 'im.vector.modular.widgets',
          },
          name: 'Modificar widgets',
        },
      ],
    };

    return [
      messagesGroup,
      callSettingsGroup,
      moderationGroup,
      roomOverviewGroup,
      roomSettingsGroup,
      otherSettingsGroup,
    ];
  }, []);

  return groups;
};
