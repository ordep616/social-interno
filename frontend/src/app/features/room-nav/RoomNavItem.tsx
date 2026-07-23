import React, { MouseEventHandler, forwardRef, useState } from 'react';
import { MatrixEvent, MsgType, Room } from 'matrix-js-sdk';
import {
  Avatar,
  Box,
  Icon,
  IconButton,
  Icons,
  Text,
  Menu,
  MenuItem,
  config,
  PopOut,
  toRem,
  Line,
  RectCords,
  Badge,
  Spinner,
} from 'folds';
import { useFocusWithin, useHover } from 'react-aria';
import FocusTrap from 'focus-trap-react';
import { useAtom, useAtomValue } from 'jotai';
import { NavItem, NavItemContent, NavItemOptions, NavLink } from '../../components/nav';
import { UnreadBadge, UnreadBadgeCenter } from '../../components/unread-badge';
import { RoomAvatar, RoomIcon } from '../../components/room-avatar';
import {
  getDirectRoomAvatarUrl,
  getRoomAvatarUrl,
  getStateEvent,
  trimReplyFromBody,
} from '../../utils/room';
import { nameInitials } from '../../utils/common';
import { useMatrixClient } from '../../hooks/useMatrixClient';
import { useRoomUnread } from '../../state/hooks/unread';
import { roomToUnreadAtom } from '../../state/room/roomToUnread';
import { getPowersLevelFromMatrixEvent, usePowerLevels } from '../../hooks/usePowerLevels';
import { copyToClipboard } from '../../utils/dom';
import { markAsRead } from '../../utils/notifications';
import { UseStateProvider } from '../../components/UseStateProvider';
import { LeaveRoomPrompt } from '../../components/leave-room-prompt';
import { useRoomTypingMember } from '../../hooks/useRoomTypingMembers';
import { TypingIndicator } from '../../components/typing-indicator';
import { stopPropagation } from '../../utils/keyboard';
import { getMatrixToRoom } from '../../plugins/matrix-to';
import { getCanonicalAliasOrRoomId, guessDmRoomUserId, isRoomAlias } from '../../utils/matrix';
import { getViaServers } from '../../plugins/via-servers';
import { useMediaAuthentication } from '../../hooks/useMediaAuthentication';
import { useSetting } from '../../state/hooks/settings';
import { settingsAtom } from '../../state/settings';
import { useOpenRoomSettings } from '../../state/hooks/roomSettings';
import { useSpaceOptionally } from '../../hooks/useSpace';
import { useRoomLatestRenderedEvent } from '../../hooks/useRoomLatestRenderedEvent';
import {
  getRoomNotificationModeIcon,
  RoomNotificationMode,
} from '../../hooks/useRoomsNotificationPreferences';
import { RoomNotificationModeSwitcher } from '../../components/RoomNotificationSwitcher';
import { getRoomCreatorsForRoomId, useRoomCreators } from '../../hooks/useRoomCreators';
import { getRoomPermissionsAPI, useRoomPermissions } from '../../hooks/useRoomPermissions';
import { InviteUserPrompt } from '../../components/invite-user-prompt';
import { useRoomName } from '../../hooks/useRoomMeta';
import { useCallMembers, useCallSession } from '../../hooks/useCall';
import { useCallEmbed, useCallStart } from '../../hooks/useCallEmbed';
import { callChatAtom } from '../../state/callEmbed';
import { useCallPreferencesAtom } from '../../state/hooks/callPreferences';
import { useAutoDiscoveryInfo } from '../../hooks/useAutoDiscoveryInfo';
import { livekitSupport } from '../../hooks/useLivekitSupport';
import { MessageEvent, StateEvent } from '../../../types/matrix/room';
import { webRTCSupported } from '../../utils/rtc';
import { timeDayMonYear, timeHourMinute, today, yesterday } from '../../utils/time';
import { Presence, useUserPresence } from '../../hooks/useUserPresence';
import * as css from './styles.css';

const cleanPreviewBody = (body: string): string => {
  const preview = trimReplyFromBody(body).replace(/\s+/g, ' ').trim();
  return preview || 'Mensagem';
};

const formatConversationTime = (
  ts: number,
  hour24Clock: boolean,
  dateFormatString: string
): string => {
  if (today(ts)) return timeHourMinute(ts, hour24Clock);
  if (yesterday(ts)) return 'Ontem';
  return timeDayMonYear(ts, dateFormatString || 'D MMM YYYY');
};

const getSenderDisplayName = (mxUserId: string | null, room: Room, event: MatrixEvent): string => {
  const senderId = event.getSender();
  if (!senderId) return '';
  if (senderId === mxUserId) return 'Você';

  return room.getMember(senderId)?.name ?? senderId;
};

const getBasePreview = (event: MatrixEvent): string => {
  if (event.isRedacted()) return 'Mensagem apagada';

  const eventType = event.getType();
  const content = event.getContent<Record<string, unknown>>();

  if (eventType === MessageEvent.RoomMessage) {
    const { body, msgtype } = content;

    if (msgtype === MsgType.Text || msgtype === MsgType.Notice) {
      return typeof body === 'string' ? cleanPreviewBody(body) : 'Mensagem';
    }
    if (msgtype === MsgType.Emote) {
      return typeof body === 'string' ? `* ${cleanPreviewBody(body)}` : 'Ação';
    }
    if (msgtype === MsgType.Image) return 'Imagem';
    if (msgtype === MsgType.Video) return 'Vídeo';
    if (msgtype === MsgType.Audio) return 'Áudio';
    if (msgtype === MsgType.File) return 'Documento';
    if (msgtype === MsgType.Location) return 'Localização';
    if (msgtype === 'm.bad.encrypted') return 'Mensagem criptografada indisponível';

    return typeof body === 'string' ? cleanPreviewBody(body) : 'Mensagem';
  }

  if (eventType === MessageEvent.RoomMessageEncrypted) return 'Mensagem criptografada';
  if (eventType === MessageEvent.Sticker) return 'Figurinha';
  if (eventType === StateEvent.RoomName) return 'Nome da conversa atualizado';
  if (eventType === StateEvent.RoomTopic) return 'Descrição da conversa atualizada';
  if (eventType === StateEvent.RoomAvatar) return 'Imagem da conversa atualizada';
  if (eventType === StateEvent.RoomMember) return 'Atividade de participantes';

  return 'Nova atividade';
};

const getConversationPreview = (
  mxUserId: string | null,
  room: Room,
  event: MatrixEvent,
  direct?: boolean
): string => {
  const preview = getBasePreview(event);
  const senderId = event.getSender();
  const senderName = getSenderDisplayName(mxUserId, room, event);
  const shouldPrefix = senderName && (!direct || senderId === mxUserId);

  return shouldPrefix ? `${senderName}: ${preview}` : preview;
};

type RoomNavItemMenuProps = {
  room: Room;
  requestClose: () => void;
  notificationMode?: RoomNotificationMode;
};
const RoomNavItemMenu = forwardRef<HTMLDivElement, RoomNavItemMenuProps>(
  ({ room, requestClose, notificationMode }, ref) => {
    const mx = useMatrixClient();
    const [hideActivity] = useSetting(settingsAtom, 'hideActivity');
    const unread = useRoomUnread(room.roomId, roomToUnreadAtom);
    const powerLevels = usePowerLevels(room);
    const creators = useRoomCreators(room);

    const permissions = useRoomPermissions(creators, powerLevels);
    const canInvite = permissions.action('invite', mx.getSafeUserId());
    const openRoomSettings = useOpenRoomSettings();
    const space = useSpaceOptionally();

    const [invitePrompt, setInvitePrompt] = useState(false);

    const handleMarkAsRead = () => {
      markAsRead(mx, room.roomId, hideActivity);
      requestClose();
    };

    const handleInvite = () => {
      setInvitePrompt(true);
    };

    const handleCopyLink = () => {
      const roomIdOrAlias = getCanonicalAliasOrRoomId(mx, room.roomId);
      const viaServers = isRoomAlias(roomIdOrAlias) ? undefined : getViaServers(room);
      copyToClipboard(getMatrixToRoom(roomIdOrAlias, viaServers));
      requestClose();
    };

    const handleRoomSettings = () => {
      openRoomSettings(room.roomId, space?.roomId);
      requestClose();
    };

    return (
      <Menu ref={ref} style={{ maxWidth: toRem(160), width: '100vw' }}>
        {invitePrompt && room && (
          <InviteUserPrompt
            room={room}
            requestClose={() => {
              setInvitePrompt(false);
              requestClose();
            }}
          />
        )}
        <Box direction="Column" gap="100" style={{ padding: config.space.S100 }}>
          <MenuItem
            onClick={handleMarkAsRead}
            size="300"
            after={<Icon size="100" src={Icons.CheckTwice} />}
            radii="300"
            disabled={!unread}
          >
            <Text style={{ flexGrow: 1 }} as="span" size="T300" truncate>
              Marcar como lida
            </Text>
          </MenuItem>
          <RoomNotificationModeSwitcher roomId={room.roomId} value={notificationMode}>
            {(handleOpen, opened, changing) => (
              <MenuItem
                size="300"
                after={
                  changing ? (
                    <Spinner size="100" variant="Secondary" />
                  ) : (
                    <Icon size="100" src={getRoomNotificationModeIcon(notificationMode)} />
                  )
                }
                radii="300"
                aria-pressed={opened}
                onClick={handleOpen}
              >
                <Text style={{ flexGrow: 1 }} as="span" size="T300" truncate>
                  Notificações
                </Text>
              </MenuItem>
            )}
          </RoomNotificationModeSwitcher>
        </Box>
        <Line variant="Surface" size="300" />
        <Box direction="Column" gap="100" style={{ padding: config.space.S100 }}>
          <MenuItem
            onClick={handleInvite}
            variant="Primary"
            fill="None"
            size="300"
            after={<Icon size="100" src={Icons.UserPlus} />}
            radii="300"
            aria-pressed={invitePrompt}
            disabled={!canInvite}
          >
            <Text style={{ flexGrow: 1 }} as="span" size="T300" truncate>
              Convidar
            </Text>
          </MenuItem>
          <MenuItem
            onClick={handleCopyLink}
            size="300"
            after={<Icon size="100" src={Icons.Link} />}
            radii="300"
          >
            <Text style={{ flexGrow: 1 }} as="span" size="T300" truncate>
              Copiar link
            </Text>
          </MenuItem>
          <MenuItem
            onClick={handleRoomSettings}
            size="300"
            after={<Icon size="100" src={Icons.Setting} />}
            radii="300"
          >
            <Text style={{ flexGrow: 1 }} as="span" size="T300" truncate>
              Configurações da conversa
            </Text>
          </MenuItem>
        </Box>
        <Line variant="Surface" size="300" />
        <Box direction="Column" gap="100" style={{ padding: config.space.S100 }}>
          <UseStateProvider initial={false}>
            {(promptLeave, setPromptLeave) => (
              <>
                <MenuItem
                  onClick={() => setPromptLeave(true)}
                  variant="Critical"
                  fill="None"
                  size="300"
                  after={<Icon size="100" src={Icons.ArrowGoLeft} />}
                  radii="300"
                  aria-pressed={promptLeave}
                >
                  <Text style={{ flexGrow: 1 }} as="span" size="T300" truncate>
                    Sair da conversa
                  </Text>
                </MenuItem>
                {promptLeave && (
                  <LeaveRoomPrompt
                    roomId={room.roomId}
                    onDone={requestClose}
                    onCancel={() => setPromptLeave(false)}
                  />
                )}
              </>
            )}
          </UseStateProvider>
        </Box>
      </Menu>
    );
  }
);

function CallChatToggle() {
  const [chat, setChat] = useAtom(callChatAtom);

  return (
    <IconButton
      onClick={() => setChat(!chat)}
      aria-pressed={chat}
      aria-label="Alternar chat"
      variant="Background"
      fill="None"
      size="300"
      radii="300"
    >
      <Icon size="50" src={Icons.Message} filled={chat} />
    </IconButton>
  );
}

type DirectPresenceIndicatorProps = {
  userId: string;
};
function DirectPresenceIndicator({ userId }: DirectPresenceIndicatorProps) {
  const presence = useUserPresence(userId);
  const online = presence?.presence === Presence.Online;

  return (
    <span
      className={css.ConversationPresenceStatus}
      data-online={online}
      role="img"
      aria-label={online ? 'Online' : 'Offline'}
    />
  );
}

type RoomNavItemProps = {
  room: Room;
  selected: boolean;
  linkPath: string;
  notificationMode?: RoomNotificationMode;
  showAvatar?: boolean;
  direct?: boolean;
};
export function RoomNavItem({
  room,
  selected,
  showAvatar,
  direct,
  notificationMode,
  linkPath,
}: RoomNavItemProps) {
  const mx = useMatrixClient();
  const myUserId = mx.getSafeUserId();
  const useAuthentication = useMediaAuthentication();
  const [hover, setHover] = useState(false);
  const { hoverProps } = useHover({ onHoverChange: setHover });
  const { focusWithinProps } = useFocusWithin({ onFocusWithinChange: setHover });
  const [menuAnchor, setMenuAnchor] = useState<RectCords>();
  const unread = useRoomUnread(room.roomId, roomToUnreadAtom);
  const typingMember = useRoomTypingMember(room.roomId).filter(
    (receipt) => receipt.userId !== mx.getUserId()
  );
  const latestEvent = useRoomLatestRenderedEvent(room);
  const [hour24Clock] = useSetting(settingsAtom, 'hour24Clock');
  const [dateFormatString] = useSetting(settingsAtom, 'dateFormatString');

  const roomName = useRoomName(room);
  const latestTs = latestEvent?.getTs();
  const conversationTime =
    typeof latestTs === 'number'
      ? formatConversationTime(latestTs, hour24Clock, dateFormatString)
      : undefined;
  const conversationPreview = latestEvent
    ? getConversationPreview(mx.getUserId(), room, latestEvent, direct)
    : 'Sem mensagens ainda';
  const typing = typingMember.length > 0;
  const directUserId = direct ? guessDmRoomUserId(room, myUserId) : undefined;
  const directPresenceUserId =
    showAvatar && directUserId && directUserId !== myUserId ? directUserId : undefined;

  const handleContextMenu: MouseEventHandler<HTMLElement> = (evt) => {
    evt.preventDefault();
    setMenuAnchor({
      x: evt.clientX,
      y: evt.clientY,
      width: 0,
      height: 0,
    });
  };

  const handleOpenMenu: MouseEventHandler<HTMLButtonElement> = (evt) => {
    setMenuAnchor(evt.currentTarget.getBoundingClientRect());
  };

  const optionsVisible = hover || !!menuAnchor;
  const callSession = useCallSession(room);
  const callMembers = useCallMembers(callSession);
  const startCall = useCallStart(direct);
  const callEmbed = useCallEmbed();
  const callPref = useAtomValue(useCallPreferencesAtom());
  const autoDiscoveryInfo = useAutoDiscoveryInfo();

  const handleStartCall: MouseEventHandler<HTMLAnchorElement> = (evt) => {
    const powerLevelsEvent = getStateEvent(room, StateEvent.RoomPowerLevels);
    const powerLevels = getPowersLevelFromMatrixEvent(powerLevelsEvent);
    const creators = getRoomCreatorsForRoomId(mx, room.roomId);
    const permissions = getRoomPermissionsAPI(creators, powerLevels);

    const hasCallPermission = permissions.stateEvent(
      StateEvent.GroupCallMemberPrefix,
      mx.getSafeUserId()
    );

    // Do not join if missing permissions or no livekit support or no webRTC support
    if (!hasCallPermission || !livekitSupport(autoDiscoveryInfo) || !webRTCSupported()) {
      return;
    }

    // Do not join if already in call
    if (callEmbed) {
      return;
    }
    // Start call in second click
    if (selected) {
      evt.preventDefault();
      startCall(room, callPref);
    }
  };

  return (
    <NavItem
      className={css.ConversationItem}
      variant="Background"
      radii="400"
      highlight={unread !== undefined}
      aria-selected={selected}
      data-hover={!!menuAnchor}
      onContextMenu={handleContextMenu}
      {...hoverProps}
      {...focusWithinProps}
    >
      <NavLink to={linkPath} onClick={room.isCallRoom() ? handleStartCall : undefined}>
        <NavItemContent className={css.ConversationContent}>
          <Box as="span" grow="Yes" alignItems="Center" gap="300">
            {showAvatar ? (
              <Box className={css.ConversationAvatarPresence} as="span">
                <Avatar className={css.ConversationAvatar} size="400" radii="Pill">
                  <RoomAvatar
                    roomId={room.roomId}
                    src={
                      direct
                        ? getDirectRoomAvatarUrl(mx, room, 96, useAuthentication)
                        : getRoomAvatarUrl(mx, room, 96, useAuthentication)
                    }
                    alt={roomName}
                    renderFallback={() => (
                      <Text as="span" size="H6">
                        {nameInitials(roomName)}
                      </Text>
                    )}
                  />
                </Avatar>
                {directPresenceUserId && <DirectPresenceIndicator userId={directPresenceUserId} />}
              </Box>
            ) : (
              <Avatar className={css.ConversationAvatar} size="400" radii="Pill">
                <RoomIcon
                  style={{
                    opacity: unread ? config.opacity.P500 : config.opacity.P300,
                  }}
                  filled={selected}
                  size="200"
                  joinRule={room.getJoinRule()}
                  roomType={room.getType()}
                />
              </Avatar>
            )}
            <Box className={css.ConversationBody} as="span" grow="Yes" direction="Column">
              <Box
                className={css.ConversationHeader}
                as="span"
                alignItems="Center"
                grow="Yes"
                gap="100"
              >
                <Text
                  className={css.ConversationName}
                  priority={unread ? '500' : '400'}
                  as="span"
                  size="T300"
                  truncate
                >
                  {roomName}
                </Text>
                {conversationTime && (
                  <Text
                    className={css.ConversationTime}
                    priority={unread ? '400' : '300'}
                    as="span"
                    size="T200"
                  >
                    {conversationTime}
                  </Text>
                )}
              </Box>
              <Box
                className={css.ConversationPreviewRow}
                as="span"
                alignItems="Center"
                grow="Yes"
                gap="200"
              >
                {typing ? (
                  <Box
                    className={css.ConversationTypingPreview}
                    as="span"
                    alignItems="Center"
                    gap="100"
                    grow="Yes"
                  >
                    <Text className={css.ConversationPreview} as="span" size="T200" truncate>
                      digitando
                    </Text>
                    <TypingIndicator size="300" />
                  </Box>
                ) : (
                  <Text
                    className={css.ConversationPreview}
                    priority={unread ? '400' : '300'}
                    as="span"
                    size="T200"
                    truncate
                  >
                    {conversationPreview}
                  </Text>
                )}
                <Box
                  className={css.ConversationMeta}
                  as="span"
                  shrink="No"
                  alignItems="Center"
                  gap="100"
                >
                  {unread && (
                    <UnreadBadgeCenter>
                      <UnreadBadge highlight={unread.highlight > 0} count={unread.total} />
                    </UnreadBadgeCenter>
                  )}
                  {notificationMode !== RoomNotificationMode.Unset && (
                    <Icon
                      size="50"
                      src={getRoomNotificationModeIcon(notificationMode)}
                      aria-label={notificationMode}
                    />
                  )}
                  {callMembers.length > 0 && (
                    <Badge variant="Critical" fill="Solid" size="400">
                      <Text as="span" size="L400" truncate>
                        {callMembers.length} Live
                      </Text>
                    </Badge>
                  )}
                </Box>
              </Box>
            </Box>
          </Box>
        </NavItemContent>
      </NavLink>
      {optionsVisible && (
        <NavItemOptions>
          {selected && (callEmbed?.roomId === room.roomId || room.isCallRoom()) && (
            <CallChatToggle />
          )}
          <PopOut
            id={`menu-${room.roomId}`}
            aria-expanded={!!menuAnchor}
            anchor={menuAnchor}
            offset={menuAnchor?.width === 0 ? 0 : undefined}
            alignOffset={menuAnchor?.width === 0 ? 0 : -5}
            position="Bottom"
            align={menuAnchor?.width === 0 ? 'Start' : 'End'}
            content={
              <FocusTrap
                focusTrapOptions={{
                  initialFocus: false,
                  returnFocusOnDeactivate: false,
                  onDeactivate: () => setMenuAnchor(undefined),
                  clickOutsideDeactivates: true,
                  isKeyForward: (evt: KeyboardEvent) => evt.key === 'ArrowDown',
                  isKeyBackward: (evt: KeyboardEvent) => evt.key === 'ArrowUp',
                  escapeDeactivates: stopPropagation,
                }}
              >
                <RoomNavItemMenu
                  room={room}
                  requestClose={() => setMenuAnchor(undefined)}
                  notificationMode={notificationMode}
                />
              </FocusTrap>
            }
          >
            <IconButton
              onClick={handleOpenMenu}
              aria-pressed={!!menuAnchor}
              aria-controls={`menu-${room.roomId}`}
              aria-label="Mais opções"
              variant="Background"
              fill="None"
              size="300"
              radii="300"
            >
              <Icon size="50" src={Icons.VerticalDots} />
            </IconButton>
          </PopOut>
        </NavItemOptions>
      )}
    </NavItem>
  );
}
