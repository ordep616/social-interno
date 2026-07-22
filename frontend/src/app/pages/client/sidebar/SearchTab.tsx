import React from 'react';
import { Icon, Icons } from 'folds';
import { useAtom } from 'jotai';
import {
  SidebarAvatar,
  SidebarItem,
  SidebarItemAction,
  SidebarItemLabel,
  SidebarItemTooltip,
} from '../../../components/sidebar';
import { searchModalAtom } from '../../../state/searchModal';

export function SearchTab() {
  const [opened, setOpen] = useAtom(searchModalAtom);

  const open = () => setOpen(true);

  return (
    <SidebarItem active={opened}>
      <SidebarItemTooltip tooltip="Buscar">
        {(triggerRef) => (
          <SidebarItemAction ref={triggerRef} onClick={open}>
            <SidebarAvatar as="span" outlined>
              <Icon src={Icons.Search} filled={opened} />
            </SidebarAvatar>
            <SidebarItemLabel>Buscar</SidebarItemLabel>
          </SidebarItemAction>
        )}
      </SidebarItemTooltip>
    </SidebarItem>
  );
}
