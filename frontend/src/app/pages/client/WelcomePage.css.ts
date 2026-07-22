import { style } from '@vanilla-extract/css';

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

export const CenterContrast = style({
  position: 'relative',
  padding: '34px 44px 38px',
  borderRadius: 8,
  selectors: {
    '&::before': {
      content: '',
      position: 'absolute',
      inset: '-28px -72px -34px',
      zIndex: -1,
      borderRadius: 8,
      background:
        'radial-gradient(ellipse at center, rgba(0, 0, 0, 0.78) 0%, rgba(0, 0, 0, 0.54) 46%, rgba(0, 0, 0, 0) 76%)',
      filter: 'blur(2px)',
      pointerEvents: 'none',
    },
  },
  '@media': {
    'screen and (max-width: 520px)': {
      padding: '26px 24px 30px',
    },
  },
});

export const NeonChatButton = style({
  minWidth: 'min(100%, 320px)',
  paddingInline: '24px',
  border: '1px solid rgba(255, 196, 142, 0.55)',
  background: 'linear-gradient(135deg, #e37a1d 0%, #d85b12 48%, #bf3f0d 100%)',
  color: '#fff',
  boxShadow: '0 10px 24px rgba(0, 0, 0, 0.32), 0 8px 20px rgba(216, 91, 18, 0.22)',
  transition: 'transform 160ms ease, box-shadow 160ms ease, filter 160ms ease',
  selectors: {
    '&:hover': {
      transform: 'translateY(-1px)',
      filter: 'brightness(1.04)',
      boxShadow: '0 12px 28px rgba(0, 0, 0, 0.36), 0 10px 22px rgba(216, 91, 18, 0.28)',
    },
    '&:focus-visible': {
      outline: '2px solid rgba(255, 255, 255, 0.86)',
      outlineOffset: '3px',
      boxShadow:
        '0 0 0 4px rgba(216, 91, 18, 0.28), 0 12px 26px rgba(0, 0, 0, 0.36), 0 10px 22px rgba(216, 91, 18, 0.26)',
    },
    '&:active': {
      transform: 'translateY(0)',
    },
  },
});

export const NeonChatButtonText = style({
  color: '#fff',
  textShadow: '0 1px 4px rgba(0, 0, 0, 0.38)',
});

export const AddUserModal = style({
  width: 'min(92vw, 420px)',
  border: '1px solid rgba(255, 255, 255, 0.12)',
  boxShadow: '0 24px 70px rgba(0, 0, 0, 0.48)',
});

export const AddUserModalBody = style({
  padding: '0 24px 24px',
});

export const AddUserModalActions = style({
  flexWrap: 'wrap',
});
