import { useMemo } from 'react';
import { StateEvent } from '../../../../types/matrix/room';
import { PermissionGroup } from '../../common-settings/permissions';

export const usePermissionGroups = (): PermissionGroup[] => {
  const groups: PermissionGroup[] = useMemo(() => {
    const messagesGroup: PermissionGroup = {
      name: 'Gerenciar',
      items: [
        {
          location: {
            state: true,
            key: StateEvent.SpaceChild,
          },
          name: 'Gerenciar salas do espaço',
        },
        {
          location: {},
          name: 'Eventos de mensagem',
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
      ],
    };

    const roomOverviewGroup: PermissionGroup = {
      name: 'Visão geral do espaço',
      items: [
        {
          location: {
            state: true,
            key: StateEvent.RoomAvatar,
          },
          name: 'Avatar do espaço',
        },
        {
          location: {
            state: true,
            key: StateEvent.RoomName,
          },
          name: 'Nome do espaço',
        },
        {
          location: {
            state: true,
            key: StateEvent.RoomTopic,
          },
          name: 'Tópico do espaço',
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
          name: 'Alterar acesso do espaço',
        },
        {
          location: {
            state: true,
            key: StateEvent.RoomCanonicalAlias,
          },
          name: 'Publicar endereço',
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
            key: StateEvent.RoomTombstone,
          },
          name: 'Atualizar espaço',
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
      ],
    };

    return [
      messagesGroup,
      moderationGroup,
      roomOverviewGroup,
      roomSettingsGroup,
      otherSettingsGroup,
    ];
  }, []);

  return groups;
};
