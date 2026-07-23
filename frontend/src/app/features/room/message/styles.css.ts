import { style } from '@vanilla-extract/css';
import { DefaultReset, color, config, toRem } from 'folds';

export const MessageBase = style({
  position: 'relative',
});
export const MessageBaseBubbleCollapsed = style({
  paddingTop: 0,
});

export const MessageOptionsBase = style([
  DefaultReset,
  {
    position: 'absolute',
    top: toRem(-30),
    right: 0,
    zIndex: 1,
  },
]);
export const MessageOptionsBar = style([
  DefaultReset,
  {
    padding: config.space.S100,
  },
]);

export const BubbleAvatarBase = style({
  paddingTop: 0,
});

export const MessageAvatar = style({
  cursor: 'pointer',
});

export const MessageQuickReaction = style({
  minWidth: toRem(32),
});

export const MessageMenuGroup = style({
  padding: config.space.S100,
});

export const MessageMenuItemText = style({
  flexGrow: 1,
});

export const MessageDeliveryStatus = style([
  DefaultReset,
  {
    alignSelf: 'flex-end',
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    minWidth: toRem(18),
    minHeight: toRem(14),
    marginTop: toRem(2),
    marginBottom: toRem(-2),
    color: 'currentColor',
    opacity: config.opacity.P400,
    transition: 'color 160ms ease, opacity 160ms ease, transform 160ms ease',

    selectors: {
      '&[data-status=seen]': {
        color: '#7dd3fc',
        minWidth: toRem(34),
        minHeight: toRem(18),
        opacity: 1,
      },
      '&[data-status=failed]': {
        color: color.Critical.Main,
        opacity: 1,
      },
    },
  },
]);

export const MessageDeliveryIcon = style({
  display: 'inline-flex',
  alignItems: 'center',
  gap: toRem(2),
  lineHeight: 0,
  transform: 'translateY(1px)',

  selectors: {
    [`${MessageDeliveryStatus}[data-status=seen] &`]: {
      gap: toRem(4),
      transform: 'translateY(1px) scale(1.2)',
      transformOrigin: 'center',
    },
  },
});

export const ReactionsContainer = style({
  selectors: {
    '&:empty': {
      display: 'none',
    },
  },
});

export const ReactionsTooltipText = style({
  wordBreak: 'break-word',
});
