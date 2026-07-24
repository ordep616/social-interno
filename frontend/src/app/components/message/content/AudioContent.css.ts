import { style } from '@vanilla-extract/css';
import { DefaultReset, config, toRem } from 'folds';

export const VoiceMessage = style([
  DefaultReset,
  {
    width: toRem(272),
    maxWidth: 'min(100%, 18rem)',
    minWidth: toRem(224),
    padding: `${config.space.S200} ${config.space.S300}`,
    borderRadius: toRem(18),
    background: '#253241',
    color: '#f4f7fb',
    boxShadow: '0 10px 24px rgba(15, 23, 42, 0.16)',

    selectors: {
      '&[data-own=true]': {
        background: 'linear-gradient(135deg, #7c3aed 0%, #6d28d9 58%, #5b21b6 100%)',
        boxShadow: '0 10px 24px rgba(91, 33, 182, 0.22)',
      },
    },

    '@media': {
      'screen and (max-width: 480px)': {
        width: 'min(100%, 16.75rem)',
        minWidth: 0,
      },
    },
  },
]);

export const VoiceBody = style({
  display: 'grid',
  gridTemplateColumns: `${toRem(40)} minmax(0, 1fr)`,
  alignItems: 'center',
  gap: config.space.S200,
});

export const PlayButton = style([
  DefaultReset,
  {
    width: toRem(38),
    height: toRem(38),
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: '50%',
    border: 0,
    background: 'rgba(244, 247, 251, 0.92)',
    color: '#253241',
    cursor: 'pointer',
    transition: 'transform 120ms ease, background-color 120ms ease',

    selectors: {
      '&:hover': {
        background: '#ffffff',
        transform: `translateY(${toRem(-1)})`,
      },
      '&:focus-visible': {
        outline: `${config.borderWidth.B600} solid rgba(255, 255, 255, 0.65)`,
        outlineOffset: toRem(2),
      },
      '&:disabled': {
        cursor: 'not-allowed',
        opacity: 0.72,
        transform: 'none',
      },
    },
  },
]);

export const Timeline = style({
  minWidth: 0,
});

export const WaveformTrack = style([
  DefaultReset,
  {
    position: 'relative',
    width: '100%',
    height: toRem(28),
    display: 'flex',
    alignItems: 'center',
    gap: toRem(2),
    cursor: 'pointer',
    touchAction: 'none',

    selectors: {
      '&:focus-visible': {
        outline: `${config.borderWidth.B600} solid rgba(255, 255, 255, 0.55)`,
        outlineOffset: toRem(2),
        borderRadius: config.radii.R300,
      },
    },
  },
]);

export const WaveformBar = style({
  flex: '1 1 0',
  minWidth: toRem(2),
  borderRadius: config.radii.R300,
  background: 'rgba(244, 247, 251, 0.38)',
});

export const WaveformProgress = style({
  position: 'absolute',
  inset: 0,
  zIndex: 1,
  display: 'flex',
  alignItems: 'center',
  gap: toRem(2),
  pointerEvents: 'none',
  willChange: 'clip-path',
});

export const WaveformProgressBar = style({
  flex: '1 1 0',
  minWidth: toRem(2),
  borderRadius: config.radii.R300,
  background: '#ffffff',
});

export const WaveformThumb = style({
  width: toRem(1),
  height: toRem(28),
  opacity: 0,
  zIndex: 2,

  selectors: {
    '&:focus-visible': {
      opacity: 1,
      background: '#ffffff',
      borderRadius: config.radii.R300,
      outline: `${config.borderWidth.B600} solid rgba(255, 255, 255, 0.55)`,
      outlineOffset: toRem(2),
    },
  },
});

export const TimeRow = style({
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  gap: config.space.S200,
  marginTop: toRem(1),
  color: 'rgba(244, 247, 251, 0.82)',
});

export const TimeAfter = style({
  display: 'inline-flex',
  alignItems: 'center',
  justifyContent: 'flex-end',
  gap: config.space.S100,
  minWidth: 0,
});

export const PlaybackRateButton = style([
  DefaultReset,
  {
    minWidth: toRem(34),
    height: toRem(20),
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: `0 ${config.space.S100}`,
    border: 0,
    borderRadius: config.radii.R300,
    background: 'rgba(244, 247, 251, 0.18)',
    color: '#ffffff',
    cursor: 'pointer',
    whiteSpace: 'nowrap',

    selectors: {
      '&:hover': {
        background: 'rgba(244, 247, 251, 0.28)',
      },
      '&:focus-visible': {
        outline: `${config.borderWidth.B600} solid rgba(255, 255, 255, 0.55)`,
        outlineOffset: toRem(2),
      },
    },
  },
]);

export const AudioElement = style({
  display: 'none',
});

export const ErrorText = style({
  marginTop: config.space.S100,
  color: '#fee2e2',
});
