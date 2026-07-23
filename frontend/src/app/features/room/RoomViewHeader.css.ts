import { style } from '@vanilla-extract/css';
import { color, config, toRem } from 'folds';

export const HeaderTopic = style({
  ':hover': {
    cursor: 'pointer',
    opacity: config.opacity.P500,
    textDecoration: 'underline',
  },
});

export const HeaderPresence = style({
  minHeight: toRem(16),
  lineHeight: toRem(16),

  selectors: {
    '&[data-online=true]': {
      color: color.Success.Main,
    },
  },
});
