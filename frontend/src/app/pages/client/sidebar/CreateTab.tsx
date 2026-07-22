import React, { MouseEventHandler, useState } from 'react';
import { Box, config, Icon, Icons, Menu, PopOut, RectCords, Text } from 'folds';
import FocusTrap from 'focus-trap-react';
import { useNavigate } from 'react-router-dom';
import {
  SidebarAvatar,
  SidebarItem,
  SidebarItemAction,
  SidebarItemLabel,
  SidebarItemTooltip,
} from '../../../components/sidebar';
import { stopPropagation } from '../../../utils/keyboard';
import { SequenceCard } from '../../../components/sequence-card';
import { SettingTile } from '../../../components/setting-tile';
import { ContainerColor } from '../../../styles/ContainerColor.css';
import { getCreatePath } from '../../pathUtils';
import { useCreateSelected } from '../../../hooks/router/useCreateSelected';

export function CreateTab() {
  const createSelected = useCreateSelected();

  const navigate = useNavigate();
  const [menuCords, setMenuCords] = useState<RectCords>();

  const handleMenu: MouseEventHandler<HTMLButtonElement> = (evt) => {
    setMenuCords(menuCords ? undefined : evt.currentTarget.getBoundingClientRect());
  };

  const handleCreateSpace = () => {
    navigate(getCreatePath());
    setMenuCords(undefined);
  };

  return (
    <SidebarItem active={createSelected}>
      <SidebarItemTooltip tooltip="Adicionar espaço">
        {(triggerRef) => (
          <PopOut
            anchor={menuCords}
            position="Right"
            align="Center"
            content={
              <FocusTrap
                focusTrapOptions={{
                  returnFocusOnDeactivate: false,
                  initialFocus: false,
                  onDeactivate: () => setMenuCords(undefined),
                  clickOutsideDeactivates: true,
                  isKeyForward: (evt: KeyboardEvent) =>
                    evt.key === 'ArrowDown' || evt.key === 'ArrowRight',
                  isKeyBackward: (evt: KeyboardEvent) =>
                    evt.key === 'ArrowUp' || evt.key === 'ArrowLeft',
                  escapeDeactivates: stopPropagation,
                }}
              >
                <Menu>
                  <Box direction="Column">
                    <SequenceCard
                      style={{ padding: config.space.S300 }}
                      variant="Surface"
                      direction="Column"
                      gap="100"
                      radii="0"
                      as="button"
                      type="button"
                      onClick={handleCreateSpace}
                    >
                      <SettingTile before={<Icon size="400" src={Icons.Space} />}>
                        <Text size="H6">Criar espaço</Text>
                        <Text size="T300" priority="300">
                          Organize conversas em um espaço da equipe.
                        </Text>
                      </SettingTile>
                    </SequenceCard>
                  </Box>
                </Menu>
              </FocusTrap>
            }
          >
            <SidebarItemAction ref={triggerRef} onClick={handleMenu}>
              <SidebarAvatar
                className={menuCords ? ContainerColor({ variant: 'Surface' }) : undefined}
                as="span"
                outlined
              >
                <Icon src={Icons.Plus} />
              </SidebarAvatar>
              <SidebarItemLabel>Adicionar espaço</SidebarItemLabel>
            </SidebarItemAction>
          </PopOut>
        )}
      </SidebarItemTooltip>
    </SidebarItem>
  );
}
