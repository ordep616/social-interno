import React, {
  KeyboardEventHandler,
  MouseEventHandler,
  PointerEventHandler,
  useEffect,
  useRef,
  useState,
} from 'react';
import { Scroll } from 'folds';

import {
  Sidebar,
  SidebarContent,
  SidebarResizeHandle,
  SidebarStackSeparator,
  SidebarStack,
} from '../../components/sidebar';
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
const EXPANDED_SIDEBAR_WIDTH = 128;
const HOVER_EXPAND_DELAY_MS = 500;

const clampSidebarWidth = (width: number): number =>
  Math.min(MAX_SIDEBAR_WIDTH, Math.max(DEFAULT_SIDEBAR_WIDTH, width));

export function SidebarNav() {
  const scrollRef = useRef<HTMLDivElement>(null);
  const hoverExpandTimerRef = useRef<number>();
  const manuallyResizedRef = useRef(false);
  const resizeStartRef = useRef({
    pointerX: 0,
    sidebarWidth: DEFAULT_SIDEBAR_WIDTH,
  });
  const [sidebarWidth, setSidebarWidth] = useState(DEFAULT_SIDEBAR_WIDTH);
  const [resizing, setResizing] = useState(false);

  const clearHoverExpandTimer = () => {
    if (hoverExpandTimerRef.current === undefined) return;
    window.clearTimeout(hoverExpandTimerRef.current);
    hoverExpandTimerRef.current = undefined;
  };

  useEffect(() => clearHoverExpandTimer, []);

  useEffect(() => {
    if (!resizing) return undefined;

    const previousCursor = document.body.style.cursor;
    const previousUserSelect = document.body.style.userSelect;

    const handlePointerMove = (evt: PointerEvent) => {
      const offset = evt.clientX - resizeStartRef.current.pointerX;
      setSidebarWidth(clampSidebarWidth(resizeStartRef.current.sidebarWidth + offset));
    };

    const handlePointerEnd = () => setResizing(false);

    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
    window.addEventListener('pointermove', handlePointerMove);
    window.addEventListener('pointerup', handlePointerEnd);
    window.addEventListener('pointercancel', handlePointerEnd);

    return () => {
      document.body.style.cursor = previousCursor;
      document.body.style.userSelect = previousUserSelect;
      window.removeEventListener('pointermove', handlePointerMove);
      window.removeEventListener('pointerup', handlePointerEnd);
      window.removeEventListener('pointercancel', handlePointerEnd);
    };
  }, [resizing]);

  const handleResizeStart: PointerEventHandler<HTMLDivElement> = (evt) => {
    if (evt.button !== 0) return;
    evt.preventDefault();
    evt.stopPropagation();
    clearHoverExpandTimer();
    manuallyResizedRef.current = true;
    resizeStartRef.current = {
      pointerX: evt.clientX,
      sidebarWidth,
    };
    setResizing(true);
  };

  const handleResizeKeyDown: KeyboardEventHandler<HTMLDivElement> = (evt) => {
    if (evt.key === 'ArrowLeft') {
      evt.preventDefault();
      clearHoverExpandTimer();
      manuallyResizedRef.current = true;
      setSidebarWidth((currentWidth) => clampSidebarWidth(currentWidth - 16));
    }

    if (evt.key === 'ArrowRight') {
      evt.preventDefault();
      clearHoverExpandTimer();
      manuallyResizedRef.current = true;
      setSidebarWidth((currentWidth) => clampSidebarWidth(currentWidth + 16));
    }

    if (evt.key === 'Home') {
      evt.preventDefault();
      clearHoverExpandTimer();
      manuallyResizedRef.current = true;
      setSidebarWidth(DEFAULT_SIDEBAR_WIDTH);
    }

    if (evt.key === 'End') {
      evt.preventDefault();
      clearHoverExpandTimer();
      manuallyResizedRef.current = true;
      setSidebarWidth(MAX_SIDEBAR_WIDTH);
    }
  };

  const handleSidebarMouseEnter: MouseEventHandler<HTMLDivElement> = () => {
    if (manuallyResizedRef.current || resizing) return;

    clearHoverExpandTimer();
    hoverExpandTimerRef.current = window.setTimeout(() => {
      hoverExpandTimerRef.current = undefined;
      setSidebarWidth(MAX_SIDEBAR_WIDTH);
    }, HOVER_EXPAND_DELAY_MS);
  };

  const handleSidebarMouseLeave: MouseEventHandler<HTMLDivElement> = () => {
    clearHoverExpandTimer();

    if (manuallyResizedRef.current || resizing) return;
    setSidebarWidth(DEFAULT_SIDEBAR_WIDTH);
  };

  const expanded = sidebarWidth >= EXPANDED_SIDEBAR_WIDTH;

  return (
    <Sidebar
      data-expanded={expanded}
      data-resizing={resizing}
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
              <SearchTab />
              <UnverifiedTab />
              <InboxTab />
              <SettingsTab />
            </SidebarStack>
          </>
        }
      />
      <SidebarResizeHandle
        role="slider"
        aria-label="Redimensionar barra lateral"
        aria-orientation="vertical"
        aria-valuemin={DEFAULT_SIDEBAR_WIDTH}
        aria-valuemax={MAX_SIDEBAR_WIDTH}
        aria-valuenow={sidebarWidth}
        data-active={resizing}
        tabIndex={0}
        onPointerDown={handleResizeStart}
        onKeyDown={handleResizeKeyDown}
      />
    </Sidebar>
  );
}
