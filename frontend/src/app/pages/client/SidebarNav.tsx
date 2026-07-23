import React, { MouseEventHandler, useEffect, useRef, useState } from 'react';
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
  StatusTab,
  UnverifiedTab,
  SearchTab,
} from './sidebar';
import { CreateTab } from './sidebar/CreateTab';

const DEFAULT_SIDEBAR_WIDTH = 66;
const MAX_SIDEBAR_WIDTH = 240;
const HOVER_EXPAND_DELAY_MS = 1500;

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
  const hoverExpandTimerRef = useRef<number>();
  const [pinnedExpanded, setPinnedExpanded] = useState(false);
  const [hoverExpanded, setHoverExpanded] = useState(false);
  const expanded = pinnedExpanded || hoverExpanded;
  const sidebarWidth = expanded ? MAX_SIDEBAR_WIDTH : DEFAULT_SIDEBAR_WIDTH;

  const clearHoverExpandTimer = () => {
    if (hoverExpandTimerRef.current === undefined) return;
    window.clearTimeout(hoverExpandTimerRef.current);
    hoverExpandTimerRef.current = undefined;
  };

  useEffect(() => clearHoverExpandTimer, []);

  const handleSidebarToggle = () => {
    clearHoverExpandTimer();

    if (expanded) {
      setPinnedExpanded(false);
      setHoverExpanded(false);
      return;
    }

    setPinnedExpanded(true);
  };

  const handleSidebarMouseEnter: MouseEventHandler<HTMLDivElement> = () => {
    if (pinnedExpanded || hoverExpanded) return;

    clearHoverExpandTimer();
    hoverExpandTimerRef.current = window.setTimeout(() => {
      hoverExpandTimerRef.current = undefined;
      setHoverExpanded(true);
    }, HOVER_EXPAND_DELAY_MS);
  };

  const handleSidebarMouseLeave: MouseEventHandler<HTMLDivElement> = () => {
    clearHoverExpandTimer();
    setHoverExpanded(false);
  };

  return (
    <Sidebar
      data-expanded={expanded}
      style={{ width: sidebarWidth }}
      onMouseEnter={handleSidebarMouseEnter}
      onMouseLeave={handleSidebarMouseLeave}
    >
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
              <StatusTab />
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
