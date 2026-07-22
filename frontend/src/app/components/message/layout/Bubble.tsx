import React, { ReactNode } from 'react';
import classNames from 'classnames';
import { Box, ContainerColor, as, color } from 'folds';
import * as css from './layout.css';

type BubbleSide = 'Left' | 'Right';

type BubbleArrowProps = {
  variant: ContainerColor;
  side: BubbleSide;
  customColor?: boolean;
};
function BubbleArrow({ variant, side, customColor }: BubbleArrowProps) {
  return (
    <svg
      className={classNames(
        side === 'Right' ? css.BubbleRightArrow : css.BubbleLeftArrow,
        customColor && css.BubbleOwnArrow
      )}
      width="9"
      height="8"
      viewBox="0 0 9 8"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M9.00004 8V0H4.82847C3.04666 0 2.15433 2.15428 3.41426 3.41421L8.00004 8H9.00004Z"
        fill={customColor ? 'currentColor' : color[variant].Container}
      />
    </svg>
  );
}

type BubbleLayoutProps = {
  align?: BubbleSide;
  highlight?: boolean;
  hideBubble?: boolean;
  before?: ReactNode;
  header?: ReactNode;
  showTail?: boolean;
};

export const BubbleLayout = as<'div', BubbleLayoutProps>(
  (
    { align = 'Left', highlight, hideBubble, before, header, showTail, children, ...props },
    ref
  ) => {
    const right = align === 'Right';
    const tail = showTail ?? !!before;

    return (
      <Box gap="300" {...props} ref={ref}>
        {!right && (
          <Box className={css.BubbleBefore} shrink="No">
            {before}
          </Box>
        )}
        <Box grow="Yes" direction="Column" alignItems={right ? 'End' : 'Start'}>
          {header}
          {hideBubble ? (
            children
          ) : (
            <Box justifyContent={right ? 'End' : 'Start'} style={{ maxWidth: '100%' }}>
              <Box
                className={classNames(
                  css.BubbleContent,
                  highlight && css.BubbleContentOwn,
                  tail && (right ? css.BubbleContentArrowRight : css.BubbleContentArrowLeft)
                )}
                direction="Column"
              >
                {tail ? (
                  <BubbleArrow variant="SurfaceVariant" side={align} customColor={highlight} />
                ) : null}
                {children}
              </Box>
            </Box>
          )}
        </Box>
      </Box>
    );
  }
);
