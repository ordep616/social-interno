import { useMemo } from 'react';
import { MessageSpacing } from '../state/settings';

export type MessageSpacingItem = {
  name: string;
  spacing: MessageSpacing;
};

export const useMessageSpacingItems = (): MessageSpacingItem[] =>
  useMemo(
    () => [
      {
        spacing: '0',
        name: 'Nenhum',
      },
      {
        spacing: '100',
        name: 'Muito pequeno',
      },
      {
        spacing: '200',
        name: 'Extra pequeno',
      },
      {
        spacing: '300',
        name: 'Pequeno',
      },
      {
        spacing: '400',
        name: 'Normal',
      },
      {
        spacing: '500',
        name: 'Grande',
      },
    ],
    []
  );
