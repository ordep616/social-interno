import { style } from '@vanilla-extract/css';
import { color, config, toRem } from 'folds';

export const CategoryButton = style({
  flexGrow: 1,
});
export const CategoryButtonIcon = style({
  opacity: config.opacity.P400,
});

export const ConversationItem = style({
  minHeight: toRem(68),
  overflow: 'hidden',

  selectors: {
    '&[aria-selected=true]': {
      boxShadow: `inset ${toRem(3)} 0 0 ${color.Primary.Main}`,
    },
  },
});

export const ConversationContent = style({
  minHeight: toRem(68),
  paddingLeft: config.space.S300,
  paddingRight: config.space.S200,
  fontWeight: config.fontWeight.W400,
});

export const ConversationAvatar = style({
  flexShrink: 0,
});

export const ConversationAvatarPresence = style({
  position: 'relative',
  display: 'inline-flex',
  flexShrink: 0,
});

export const ConversationPresenceStatus = style({
  position: 'absolute',
  right: toRem(-1),
  bottom: toRem(-1),
  zIndex: 1,

  width: toRem(14),
  height: toRem(14),
  display: 'inline-flex',
  alignItems: 'center',
  justifyContent: 'center',

  borderRadius: config.radii.Pill,
  backgroundColor: '#343941',
  boxShadow: `0 0 0 ${toRem(1)} ${color.Background.Container}`,
  pointerEvents: 'none',

  selectors: {
    '&::after': {
      content: '',
      width: toRem(8),
      height: toRem(8),
      borderRadius: config.radii.Pill,
      backgroundColor: '#a7adb7',
      transition: 'background-color 160ms ease',
    },
    '&[data-online=true]::after': {
      backgroundColor: color.Success.Main,
    },
  },
});

export const ConversationBody = style({
  minWidth: 0,
  overflow: 'hidden',
});

export const ConversationHeader = style({
  minWidth: 0,
});

export const ConversationName = style({
  minWidth: 0,
});

export const ConversationTime = style({
  marginLeft: config.space.S200,
  whiteSpace: 'nowrap',
});

export const ConversationPreviewRow = style({
  minWidth: 0,
  marginTop: toRem(2),
});

export const ConversationPreview = style({
  minWidth: 0,
  overflow: 'hidden',
  textOverflow: 'ellipsis',
  whiteSpace: 'nowrap',
});

export const ConversationTypingPreview = style({
  color: color.Success.Main,
  minWidth: 0,
});

export const ConversationMeta = style({
  marginLeft: config.space.S200,
});
