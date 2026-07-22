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
