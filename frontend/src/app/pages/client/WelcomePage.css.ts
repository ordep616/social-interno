import { style } from '@vanilla-extract/css';

export const WelcomePageRoot = style({
  minHeight: '100%',
  position: 'relative',
  overflow: 'hidden',
  isolation: 'isolate',
  backgroundColor: '#050505',
  backgroundPosition: 'center',
  backgroundRepeat: 'no-repeat',
  backgroundSize: 'cover',
});

export const CenterStage = style({
  position: 'absolute',
  inset: 0,
  display: 'grid',
  placeItems: 'center',
  padding: '24px',
  pointerEvents: 'none',
});

export const CenterLockup = style({
  position: 'relative',
  display: 'grid',
  justifyItems: 'center',
  gap: '20px',
  transform: 'translateY(-3vh)',
  selectors: {
    '&::before': {
      content: '',
      position: 'absolute',
      inset: '-40px -96px -28px',
      zIndex: -1,
      background:
        'radial-gradient(ellipse at center, rgba(0, 0, 0, 0.82) 0%, rgba(0, 0, 0, 0.62) 42%, rgba(0, 0, 0, 0) 76%)',
      pointerEvents: 'none',
    },
  },
  '@media': {
    'screen and (max-width: 520px)': {
      gap: '16px',
      transform: 'translateY(-7vh)',
    },
  },
});

export const AppLogo = style({
  width: 'clamp(132px, 15vw, 184px)',
  height: 'clamp(132px, 15vw, 184px)',
  borderRadius: '50%',
  objectFit: 'cover',
  boxShadow: '0 22px 46px rgba(0, 0, 0, 0.58), 0 0 0 1px rgba(255, 255, 255, 0.12)',
});

export const WelcomeTitle = style({
  margin: 0,
  color: '#f5f5f5',
  fontSize: 'clamp(25px, 3vw, 34px)',
  fontWeight: 700,
  lineHeight: 1.12,
  textAlign: 'center',
  textShadow: '0 2px 8px rgba(0, 0, 0, 0.88), 0 0 18px rgba(0, 0, 0, 0.9)',
});

export const ExplorerNetLogo = style({
  position: 'absolute',
  right: 'clamp(24px, 5vw, 64px)',
  bottom: 'clamp(22px, 5vh, 48px)',
  width: 'clamp(190px, 22vw, 284px)',
  height: 'auto',
  filter: 'drop-shadow(0 12px 22px rgba(0, 0, 0, 0.55))',
  pointerEvents: 'none',
  '@media': {
    'screen and (max-width: 640px)': {
      right: '50%',
      bottom: '28px',
      width: 'min(220px, calc(100vw - 48px))',
      transform: 'translateX(50%)',
    },
  },
});

export const ScreenReaderOnly = style({
  position: 'absolute',
  width: 1,
  height: 1,
  padding: 0,
  margin: -1,
  overflow: 'hidden',
  clip: 'rect(0, 0, 0, 0)',
  whiteSpace: 'nowrap',
  border: 0,
});
