import React from 'react';
import { Box, Text } from 'folds';
import { EmojiBoardTab } from '../types';
import * as css from './styles.css';

export function EmojiBoardTabs({
  tab,
  onTabChange,
}: {
  tab: EmojiBoardTab;
  onTabChange: (tab: EmojiBoardTab) => void;
}) {
  return (
    <Box className={css.EmojiBoardTabs} gap="100">
      <button
        className={css.EmojiBoardTabButton}
        data-active={tab === EmojiBoardTab.Emoji}
        type="button"
        onClick={() => onTabChange(EmojiBoardTab.Emoji)}
      >
        <Text as="span" size="L400">
          Emoji
        </Text>
      </button>
      <button
        className={css.EmojiBoardTabButton}
        data-active={tab === EmojiBoardTab.Sticker}
        type="button"
        onClick={() => onTabChange(EmojiBoardTab.Sticker)}
      >
        <Text as="span" size="L400">
          Stickers
        </Text>
      </button>
    </Box>
  );
}
