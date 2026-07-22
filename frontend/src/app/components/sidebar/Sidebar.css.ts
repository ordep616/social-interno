import { createVar, style } from '@vanilla-extract/css';
import { recipe, RecipeVariants } from '@vanilla-extract/recipes';
import { color, config, DefaultReset, Disabled, FocusOutline, toRem } from 'folds';
import { ContainerColor } from '../../styles/ContainerColor.css';

export const Sidebar = style([
  DefaultReset,
  {
    width: toRem(66),
    minWidth: toRem(66),
    maxWidth: toRem(240),
    flexShrink: 0,
    backgroundColor: color.Background.Container,
    borderRight: `${config.borderWidth.B300} solid ${color.Background.ContainerLine}`,
    position: 'relative',

    display: 'flex',
    flexDirection: 'column',
    color: color.Background.OnContainer,
    transition: 'width 120ms ease',

    selectors: {
      '&[data-resizing=true]': {
        transition: 'none',
      },
    },
  },
]);

export const SidebarResizeHandle = style({
  position: 'absolute',
  top: 0,
  right: toRem(-4),
  bottom: 0,
  zIndex: 2,
  width: toRem(8),
  padding: 0,
  border: 0,
  background: 'transparent',
  cursor: 'col-resize',
  touchAction: 'none',

  selectors: {
    '&::after': {
      content: '',
      position: 'absolute',
      top: 0,
      bottom: 0,
      left: '50%',
      width: config.borderWidth.B300,
      backgroundColor: 'transparent',
      transform: 'translateX(-50%)',
    },
    '&:hover::after, &[data-active=true]::after': {
      backgroundColor: color.Primary.Main,
    },
  },
});

export const SidebarStack = style([
  DefaultReset,
  {
    width: '100%',
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    alignItems: 'center',
    gap: config.space.S300,
    padding: `${config.space.S300} 0`,

    selectors: {
      [`${Sidebar}[data-expanded=true] &`]: {
        alignItems: 'stretch',
        paddingLeft: config.space.S300,
        paddingRight: config.space.S300,
      },
    },
  },
]);

const DropLineDist = createVar();
export const DropTarget = style({
  vars: {
    [DropLineDist]: toRem(-8),
  },

  selectors: {
    '&[data-inside-folder=true]': {
      vars: {
        [DropLineDist]: toRem(-6),
      },
    },
    '&[data-drop-child=true]': {
      outline: `${config.borderWidth.B700} solid ${color.Success.Main}`,
      borderRadius: config.radii.R400,
    },
    '&[data-drop-above=true]::after, &[data-drop-below=true]::after': {
      content: '',
      display: 'block',
      position: 'absolute',
      left: toRem(0),
      width: '100%',
      height: config.borderWidth.B700,
      backgroundColor: color.Success.Main,
    },
    '&[data-drop-above=true]::after': {
      top: DropLineDist,
    },
    '&[data-drop-below=true]::after': {
      bottom: DropLineDist,
    },
  },
});

const PUSH_X = 2;
export const SidebarItem = recipe({
  base: [
    DefaultReset,
    {
      minWidth: toRem(42),
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      position: 'relative',
      transition: 'transform 200ms cubic-bezier(0, 0.8, 0.67, 0.97)',

      selectors: {
        '&:hover': {
          transform: `translateX(${toRem(PUSH_X)})`,
        },
        '&::before': {
          content: '',
          display: 'none',
          position: 'absolute',
          left: toRem(-11.5 - PUSH_X),
          width: toRem(3 + PUSH_X),
          height: toRem(16),
          borderRadius: `0 ${toRem(4)} ${toRem(4)} 0`,
          background: 'CurrentColor',
          transition: 'height 200ms linear',
        },
        '&:hover::before': {
          display: 'block',
          width: toRem(3),
        },
        [`${Sidebar}[data-expanded=true] &`]: {
          width: '100%',
          minWidth: 0,
        },
        [`${Sidebar}[data-expanded=true] &:hover`]: {
          transform: 'none',
        },
      },
    },
    Disabled,
    DropTarget,
  ],
  variants: {
    active: {
      true: {
        selectors: {
          '&::before': {
            display: 'block',
            height: toRem(24),
          },
          '&:hover::before': {
            width: toRem(3 + PUSH_X),
          },
        },
      },
    },
  },
});
export type SidebarItemVariants = RecipeVariants<typeof SidebarItem>;

export const SidebarItemAction = style([
  DefaultReset,
  {
    width: toRem(42),
    minHeight: toRem(42),
    border: 0,
    padding: 0,
    background: 'transparent',
    color: 'inherit',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: config.radii.R400,
    cursor: 'pointer',
    textAlign: 'start',

    selectors: {
      '&:hover': {
        textDecoration: 'none',
      },
      [`${Sidebar}[data-expanded=true] &`]: {
        width: '100%',
        minWidth: 0,
        justifyContent: 'flex-start',
        gap: config.space.S300,
      },
    },
  },
  FocusOutline,
]);

export const SidebarItemLabel = style([
  DefaultReset,
  {
    display: 'none',
    minWidth: 0,
    flex: '1 1 auto',
    color: color.Background.OnContainer,

    selectors: {
      [`${Sidebar}[data-expanded=true] &`]: {
        display: 'block',
      },
    },
  },
]);

export const SidebarItemBadge = recipe({
  base: [
    DefaultReset,
    {
      pointerEvents: 'none',
      position: 'absolute',
      zIndex: 1,
      lineHeight: 0,
    },
  ],
  variants: {
    hasCount: {
      true: {
        top: toRem(-6),
        left: toRem(-6),
      },
      false: {
        top: toRem(-2),
        left: toRem(-2),
      },
    },
  },
  defaultVariants: {
    hasCount: false,
  },
});
export type SidebarItemBadgeVariants = RecipeVariants<typeof SidebarItemBadge>;

export const SidebarAvatar = recipe({
  base: [
    {
      flexShrink: 0,

      selectors: {
        'button&': {
          cursor: 'pointer',
        },
      },
    },
  ],
  variants: {
    size: {
      '200': {
        width: toRem(16),
        height: toRem(16),
        fontSize: toRem(10),
        lineHeight: config.lineHeight.T200,
        letterSpacing: config.letterSpacing.T200,
      },
      '300': {
        width: toRem(34),
        height: toRem(34),
      },
      '400': {
        width: toRem(42),
        height: toRem(42),
      },
    },
    outlined: {
      true: {
        border: `${config.borderWidth.B300} solid ${color.Background.ContainerLine}`,
      },
    },
  },
  defaultVariants: {
    size: '400',
  },
});
export type SidebarAvatarVariants = RecipeVariants<typeof SidebarAvatar>;

export const SidebarFolder = recipe({
  base: [
    ContainerColor({ variant: 'Background' }),
    {
      padding: config.space.S100,
      width: toRem(42),
      minHeight: toRem(42),
      display: 'flex',
      flexWrap: 'wrap',
      outline: `${config.borderWidth.B300} solid ${color.Background.ContainerLine}`,
      position: 'relative',

      selectors: {
        'button&': {
          cursor: 'pointer',
        },
      },
    },
    FocusOutline,
    DropTarget,
  ],
  variants: {
    state: {
      Close: {
        gap: toRem(2),
        borderRadius: config.radii.R400,
      },
      Open: {
        paddingLeft: 0,
        paddingRight: 0,
        flexDirection: 'column',
        alignItems: 'center',
        gap: config.space.S200,
        borderRadius: config.radii.R500,
        selectors: {
          [`${Sidebar}[data-expanded=true] &`]: {
            width: '100%',
            alignItems: 'stretch',
          },
        },
      },
    },
  },
  defaultVariants: {
    state: 'Close',
  },
});
export type SidebarFolderVariants = RecipeVariants<typeof SidebarFolder>;

export const SidebarFolderDropTarget = recipe({
  base: {
    width: '100%',
    height: toRem(8),
    position: 'absolute',
    left: 0,
  },
  variants: {
    position: {
      Top: {
        top: toRem(-4),
      },
      Bottom: {
        bottom: toRem(-4),
      },
    },
  },
});
export type SidebarFolderDropTargetVariants = RecipeVariants<typeof SidebarFolderDropTarget>;
