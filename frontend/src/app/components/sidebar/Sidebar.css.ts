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
    transition: 'width 240ms ease',
  },
]);

export const SidebarStack = style([
  DefaultReset,
  {
    width: '100%',
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    alignItems: 'center',
    gap: config.space.S200,
    padding: `${config.space.S300} ${config.space.S200}`,

    selectors: {
      [`${Sidebar}[data-expanded=true] &`]: {
        alignItems: 'stretch',
        paddingLeft: config.space.S300,
        paddingRight: config.space.S300,
      },
    },
  },
]);

export const SidebarToggleIcon = style({
  transformOrigin: 'center',
  transition: 'transform 180ms ease',

  selectors: {
    [`${Sidebar}[data-expanded=true] &`]: {
      transform: 'rotate(180deg)',
    },
  },
});

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
      borderRadius: config.radii.R500,
      color: color.Background.OnContainer,
      transition: 'color 160ms ease, transform 160ms ease',

      selectors: {
        '&:hover': {
          color: color.Primary.Main,
        },
        '&::before': {
          content: '',
          position: 'absolute',
          left: toRem(-8 - PUSH_X),
          width: toRem(3),
          height: toRem(16),
          borderRadius: `0 ${toRem(4)} ${toRem(4)} 0`,
          backgroundColor: color.Primary.Main,
          opacity: 0,
          transform: `scaleY(0.65) translateX(${toRem(-2)})`,
          transition: 'height 160ms ease, opacity 160ms ease, transform 160ms ease',
        },
        '&:hover::before': {
          opacity: config.opacity.P300,
          transform: 'scaleY(1) translateX(0)',
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
        color: color.Primary.Main,
        selectors: {
          '&::before': {
            height: toRem(26),
            opacity: 1,
            transform: 'scaleY(1) translateX(0)',
          },
          '&:hover::before': {
            opacity: 1,
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
    transition: 'background-color 160ms ease, color 160ms ease, box-shadow 160ms ease',

    selectors: {
      '&:hover': {
        backgroundColor: color.Background.ContainerHover,
        textDecoration: 'none',
      },
      '&:active': {
        backgroundColor: color.Background.ContainerActive,
      },
      [`${SidebarItem({ active: true })} &`]: {
        backgroundColor: color.Background.ContainerActive,
        boxShadow: `inset 0 0 0 ${config.borderWidth.B300} ${color.Primary.ContainerLine}`,
      },
      [`${Sidebar}[data-expanded=true] &`]: {
        width: '100%',
        minWidth: 0,
        minHeight: toRem(44),
        paddingLeft: config.space.S200,
        paddingRight: config.space.S300,
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
    display: 'block',
    minWidth: 0,
    maxWidth: 0,
    flex: '0 1 auto',
    overflow: 'hidden',
    color: color.Background.OnContainer,
    opacity: 0,
    transform: `translateX(${toRem(-4)})`,
    transition: 'max-width 220ms ease, opacity 160ms ease, transform 160ms ease',

    selectors: {
      [`${Sidebar}[data-expanded=true] &`]: {
        maxWidth: toRem(160),
        flex: '1 1 auto',
        opacity: 1,
        transform: 'translateX(0)',
      },
      [`${SidebarItem({ active: true })} &`]: {
        color: color.Primary.Main,
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
      transition: 'background-color 160ms ease, border-color 160ms ease, transform 160ms ease',

      selectors: {
        'button&': {
          cursor: 'pointer',
        },
        [`${SidebarItem()}:hover &`]: {
          borderColor: color.Primary.ContainerLine,
        },
        [`${SidebarItem({ active: true })} &`]: {
          borderColor: color.Primary.ContainerLine,
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
