import { keyframes, style } from '@vanilla-extract/css';

export const WelcomePageRoot = style({
  position: 'relative',
  overflow: 'hidden',
  backgroundColor: '#050505',
  backgroundPosition: 'center',
  backgroundRepeat: 'no-repeat',
  backgroundSize: 'cover',
});

export const WelcomeTitle = style({
  color: '#f5f5f5',
  textShadow: '0 2px 10px rgba(0, 0, 0, 0.86), 0 0 18px rgba(0, 0, 0, 0.74)',
});

const neonPulse = keyframes({
  '0%, 100%': {
    boxShadow:
      '0 0 10px rgba(255, 90, 0, 0.75), 0 0 26px rgba(255, 90, 0, 0.42), 0 10px 28px rgba(255, 90, 0, 0.28)',
  },
  '50%': {
    boxShadow:
      '0 0 18px rgba(255, 166, 0, 0.95), 0 0 42px rgba(255, 90, 0, 0.62), 0 12px 34px rgba(255, 90, 0, 0.36)',
  },
});

export const NeonChatButton = style({
  minWidth: 'min(100%, 320px)',
  paddingInline: '24px',
  border: '1px solid rgba(255, 255, 255, 0.78)',
  background: 'linear-gradient(135deg, #ff9d00 0%, #ff5a00 42%, #ff2f00 100%)',
  color: '#fff',
  animation: `${neonPulse} 2.1s ease-in-out infinite`,
  transition: 'transform 160ms ease, box-shadow 160ms ease, filter 160ms ease',
  selectors: {
    '&:hover': {
      transform: 'translateY(-2px) scale(1.03)',
      filter: 'brightness(1.1)',
      boxShadow:
        '0 0 20px rgba(255, 166, 0, 1), 0 0 54px rgba(255, 90, 0, 0.78), 0 16px 36px rgba(255, 90, 0, 0.42)',
    },
    '&:focus-visible': {
      outline: '2px solid #fff',
      outlineOffset: '3px',
      boxShadow:
        '0 0 0 4px rgba(255, 90, 0, 0.34), 0 0 26px rgba(255, 166, 0, 1), 0 0 58px rgba(255, 90, 0, 0.82)',
    },
    '&:active': {
      transform: 'translateY(0) scale(0.99)',
    },
  },
});

export const NeonChatButtonText = style({
  color: '#fff',
  textShadow: '0 0 8px rgba(255, 255, 255, 0.9), 0 0 14px rgba(255, 247, 214, 0.6)',
});
