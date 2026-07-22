import React, { useRef, useState } from 'react';
import { Icon, Icons, Scroll } from 'folds';

import {
  Sidebar,
  SidebarAvatar,
  SidebarContent,
  SidebarItem,
  SidebarItemAction,
  SidebarItemLabel,
  SidebarItemTooltip,
  SidebarStackSeparator,
  SidebarStack,
} from '../../components/sidebar';
import * as sidebarCss from '../../components/sidebar/Sidebar.css';
import {
  DirectTab,
  HomeTab,
  SpaceTabs,
  InboxTab,
  SettingsTab,
  UnverifiedTab,
  SearchTab,
} from './sidebar';
import { CreateTab } from './sidebar/CreateTab';

const DEFAULT_SIDEBAR_WIDTH = 66;
const MAX_SIDEBAR_WIDTH = 240;

type SidebarToggleTabProps = {
  expanded: boolean;
  onToggle: () => void;
};

function SidebarToggleTab({ expanded, onToggle }: SidebarToggleTabProps) {
  const label = expanded ? 'Recolher barra lateral' : 'Expandir barra lateral';

  return (
    <SidebarItem>
      <SidebarItemTooltip tooltip={label}>
        {(triggerRef) => (
          <SidebarItemAction
            ref={triggerRef}
            aria-label={label}
            aria-expanded={expanded}
            onClick={onToggle}
          >
            <SidebarAvatar as="span" outlined>
              <Icon className={sidebarCss.SidebarToggleIcon} src={Icons.ChevronRight} />
            </SidebarAvatar>
            <SidebarItemLabel>{label}</SidebarItemLabel>
          </SidebarItemAction>
        )}
      </SidebarItemTooltip>
    </SidebarItem>
  );
}

export function SidebarNav() {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [expanded, setExpanded] = useState(false);
  const sidebarWidth = expanded ? MAX_SIDEBAR_WIDTH : DEFAULT_SIDEBAR_WIDTH;
  const handleSidebarToggle = () => setExpanded((current) => !current);

  return (
    <Sidebar data-expanded={expanded} style={{ width: sidebarWidth }}>
      <SidebarContent
        scrollable={
          <Scroll ref={scrollRef} variant="Background" size="0">
            <SidebarStack>
              <HomeTab />
              <DirectTab />
            </SidebarStack>
            <SpaceTabs scrollRef={scrollRef} />
            <SidebarStackSeparator />
            <SidebarStack>
              <CreateTab />
            </SidebarStack>
          </Scroll>
        }
        sticky={
          <>
            <SidebarStackSeparator />
            <SidebarStack>
              <SidebarToggleTab expanded={expanded} onToggle={handleSidebarToggle} />
              <SearchTab />
              <UnverifiedTab />
              <InboxTab />
              <SettingsTab />
            </SidebarStack>
          </>
        }
      />
    </Sidebar>
  );
}
