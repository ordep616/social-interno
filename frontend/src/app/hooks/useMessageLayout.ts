import { useMemo } from 'react';
import { MessageLayout } from '../state/settings';

export type MessageLayoutItem = {
  name: string;
  layout: MessageLayout;
};

export const useMessageLayoutItems = (): MessageLayoutItem[] =>
  useMemo(
    () => [
      {
        layout: MessageLayout.Modern,
        name: 'Moderno',
      },
      {
        layout: MessageLayout.Compact,
        name: 'Compacto',
      },
      {
        layout: MessageLayout.Bubble,
        name: 'Bolhas',
      },
    ],
    []
  );
