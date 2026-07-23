import React, { useEffect, useState } from 'react';
import {
  Avatar,
  Box,
  Button,
  Header,
  Icon,
  IconButton,
  IconSrc,
  Icons,
  Modal,
  Overlay,
  OverlayBackdrop,
  OverlayCenter,
  Spinner,
  Text,
  color,
  config,
} from 'folds';
import FocusTrap from 'focus-trap-react';
import {
  SidebarAvatar,
  SidebarItem,
  SidebarItemAction,
  SidebarItemLabel,
  SidebarItemTooltip,
} from '../../../components/sidebar';
import { UserAvatar } from '../../../components/user-avatar';
import { AvatarPresence, PresenceBadge } from '../../../components/presence';
import { useMatrixClient } from '../../../hooks/useMatrixClient';
import { Presence, UserPresence, useUserPresence } from '../../../hooks/useUserPresence';
import { useUserProfile } from '../../../hooks/useUserProfile';
import { useMediaAuthentication } from '../../../hooks/useMediaAuthentication';
import { getMxIdLocalPart, mxcUrlToHttp } from '../../../utils/matrix';
import { nameInitials } from '../../../utils/common';
import { stopPropagation } from '../../../utils/keyboard';

type PresenceOption = {
  value: Presence;
  label: string;
  description: string;
  icon: IconSrc;
};

const PRESENCE_OPTIONS: PresenceOption[] = [
  {
    value: Presence.Online,
    label: 'Online',
    description: 'Disponivel para conversar.',
    icon: Icons.Check,
  },
  {
    value: Presence.Unavailable,
    label: 'Ausente',
    description: 'Mostra que voce esta temporariamente indisponivel.',
    icon: Icons.Clock,
  },
  {
    value: Presence.Offline,
    label: 'Offline',
    description: 'Oculta sua disponibilidade atual.',
    icon: Icons.EyeBlind,
  },
];

const getPresenceLabel = (presence: Presence): string =>
  PRESENCE_OPTIONS.find((option) => option.value === presence)?.label ?? 'Offline';

const getPresenceErrorMessage = (error: unknown): string => {
  if (error instanceof Error && error.message) return error.message;
  return 'Nao foi possivel atualizar seu status.';
};

type StatusDialogProps = {
  requestClose: () => void;
  userId: string;
  userPresence?: UserPresence;
  currentPresence: Presence;
  onPresenceChange: (presence: Presence) => void;
};

function StatusDialog({
  requestClose,
  userId,
  userPresence,
  currentPresence,
  onPresenceChange,
}: StatusDialogProps) {
  const mx = useMatrixClient();
  const useAuthentication = useMediaAuthentication();
  const profile = useUserProfile(userId);
  const [changingPresence, setChangingPresence] = useState<Presence>();
  const [error, setError] = useState<string>();

  const displayName = profile.displayName ?? getMxIdLocalPart(userId) ?? userId;
  const avatarUrl = profile.avatarUrl
    ? mxcUrlToHttp(mx, profile.avatarUrl, useAuthentication, 96, 96, 'crop') ?? undefined
    : undefined;

  const handlePresenceChange = async (presence: Presence) => {
    if (changingPresence || presence === currentPresence) return;

    setError(undefined);
    setChangingPresence(presence);

    try {
      await mx.setPresence({ presence });
      await mx.setSyncPresence(presence as unknown as Parameters<typeof mx.setSyncPresence>[0]);
      onPresenceChange(presence);
    } catch (err) {
      setError(getPresenceErrorMessage(err));
    } finally {
      setChangingPresence(undefined);
    }
  };

  return (
    <Overlay open backdrop={<OverlayBackdrop />}>
      <OverlayCenter>
        <FocusTrap
          focusTrapOptions={{
            initialFocus: false,
            clickOutsideDeactivates: true,
            onDeactivate: requestClose,
            escapeDeactivates: stopPropagation,
          }}
        >
          <Modal size="300" variant="Background">
            <Box direction="Column">
              <Header
                size="500"
                style={{
                  padding: config.space.S200,
                  paddingLeft: config.space.S400,
                }}
              >
                <Box grow="Yes">
                  <Text size="H4">Status</Text>
                </Box>
                <Box shrink="No">
                  <IconButton
                    aria-label="Fechar status"
                    size="300"
                    radii="300"
                    onClick={requestClose}
                  >
                    <Icon src={Icons.Cross} />
                  </IconButton>
                </Box>
              </Header>
              <Box
                direction="Column"
                gap="500"
                style={{
                  padding: config.space.S400,
                  paddingTop: config.space.S300,
                }}
              >
                <Box alignItems="Center" gap="300">
                  <AvatarPresence
                    badge={
                      <PresenceBadge presence={currentPresence} status={userPresence?.status} />
                    }
                  >
                    <Avatar size="500">
                      <UserAvatar
                        userId={userId}
                        src={avatarUrl}
                        alt={displayName}
                        renderFallback={() => <Text size="H3">{nameInitials(displayName)}</Text>}
                      />
                    </Avatar>
                  </AvatarPresence>
                  <Box direction="Column" gap="100" style={{ minWidth: 0 }}>
                    <Text size="H4" truncate>
                      {displayName}
                    </Text>
                    <Text size="T300" priority="300" truncate>
                      {getPresenceLabel(currentPresence)}
                    </Text>
                  </Box>
                </Box>
                <Box direction="Column" gap="200">
                  {PRESENCE_OPTIONS.map((option) => {
                    const selected = option.value === currentPresence;
                    const loading = changingPresence === option.value;

                    return (
                      <Button
                        key={option.value}
                        variant={selected ? 'Primary' : 'Secondary'}
                        fill={selected ? 'Soft' : 'None'}
                        size="400"
                        radii="400"
                        aria-pressed={selected}
                        disabled={!!changingPresence}
                        onClick={() => handlePresenceChange(option.value)}
                        before={
                          loading ? (
                            <Spinner size="100" variant={selected ? 'Primary' : 'Secondary'} />
                          ) : (
                            <Icon size="100" src={option.icon} filled={selected} />
                          )
                        }
                        after={
                          selected && !loading ? <Icon size="100" src={Icons.Check} /> : undefined
                        }
                      >
                        <Box direction="Column" gap="0" style={{ minWidth: 0 }}>
                          <Text as="span" size="B400" truncate>
                            {option.label}
                          </Text>
                          <Text as="span" size="T200" priority="300" truncate>
                            {option.description}
                          </Text>
                        </Box>
                      </Button>
                    );
                  })}
                </Box>
                {error && (
                  <Text size="T300" style={{ color: color.Critical.Main }}>
                    {error}
                  </Text>
                )}
              </Box>
            </Box>
          </Modal>
        </FocusTrap>
      </OverlayCenter>
    </Overlay>
  );
}

export function StatusTab() {
  const mx = useMatrixClient();
  const userId = mx.getSafeUserId();
  const userPresence = useUserPresence(userId);
  const [optimisticPresence, setOptimisticPresence] = useState<Presence>();
  const [status, setStatus] = useState(false);
  const currentPresence = optimisticPresence ?? userPresence?.presence ?? Presence.Offline;

  useEffect(() => {
    if (userPresence?.presence === optimisticPresence) {
      setOptimisticPresence(undefined);
    }
  }, [optimisticPresence, userPresence?.presence]);

  const openStatus = () => setStatus(true);
  const closeStatus = () => setStatus(false);

  return (
    <SidebarItem active={status}>
      <SidebarItemTooltip tooltip="Status do usuário">
        {(triggerRef) => (
          <SidebarItemAction ref={triggerRef} onClick={openStatus}>
            <AvatarPresence
              as="span"
              variant="Background"
              badge={
                <PresenceBadge
                  presence={currentPresence}
                  status={userPresence?.status}
                  size="200"
                />
              }
            >
              <SidebarAvatar as="span" outlined>
                <Icon src={Icons.User} filled={status} />
              </SidebarAvatar>
            </AvatarPresence>
            <SidebarItemLabel>Status</SidebarItemLabel>
          </SidebarItemAction>
        )}
      </SidebarItemTooltip>
      {status && (
        <StatusDialog
          requestClose={closeStatus}
          userId={userId}
          userPresence={userPresence}
          currentPresence={currentPresence}
          onPresenceChange={setOptimisticPresence}
        />
      )}
    </SidebarItem>
  );
}
