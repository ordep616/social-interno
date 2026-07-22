import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  Header,
  Icon,
  IconButton,
  Icons,
  Modal,
  Overlay,
  OverlayBackdrop,
  OverlayCenter,
  Text,
  config,
} from 'folds';
import FocusTrap from 'focus-trap-react';
import { Page, PageHeroSection } from '../../components/page';
import { getDirectCreatePath } from '../pathUtils';
import { stopPropagation } from '../../utils/keyboard';
import {
  AddUserModal,
  AddUserModalActions,
  AddUserModalBody,
  CenterContrast,
  NeonChatButton,
  NeonChatButtonText,
  WelcomePageRoot,
  WelcomeTitle,
} from './WelcomePage.css';
import WelcomeBackground from '../../../../public/res/background/betweenus-welcome.jpeg';
import AppLogo from '../../../../public/res/logo/company-logo.png';

export function WelcomePage() {
  const navigate = useNavigate();
  const [addUserModal, setAddUserModal] = useState(false);

  const closeAddUserModal = () => setAddUserModal(false);
  const openAddUserArea = () => {
    setAddUserModal(false);
    navigate(getDirectCreatePath());
  };

  return (
    <>
      <Page className={WelcomePageRoot} style={{ backgroundImage: `url(${WelcomeBackground})` }}>
        <Box
          grow="Yes"
          style={{ padding: config.space.S700 }}
          alignItems="Center"
          justifyContent="Center"
        >
          <PageHeroSection>
            <Box className={CenterContrast} direction="Column" alignItems="Center" gap="500">
              <img
                width="160"
                height="160"
                src={AppLogo}
                alt="Betweenus logo"
                style={{ borderRadius: '50%', objectFit: 'cover' }}
              />
              <Text className={WelcomeTitle} as="h1" align="Center" size="H2">
                Bem-vindo ao Betweenus
              </Text>
              <Button
                className={NeonChatButton}
                size="500"
                radii="300"
                onClick={() => setAddUserModal(true)}
              >
                <Text className={NeonChatButtonText} as="span" size="B400" truncate>
                  Comece a conversar agora!
                </Text>
              </Button>
            </Box>
          </PageHeroSection>
        </Box>
      </Page>

      {addUserModal && (
        <Overlay open backdrop={<OverlayBackdrop />}>
          <OverlayCenter>
            <FocusTrap
              focusTrapOptions={{
                initialFocus: false,
                clickOutsideDeactivates: true,
                onDeactivate: closeAddUserModal,
                escapeDeactivates: stopPropagation,
              }}
            >
              <Modal className={AddUserModal} size="300" variant="Background">
                <Box direction="Column">
                  <Header
                    size="500"
                    style={{
                      padding: config.space.S200,
                      paddingLeft: config.space.S400,
                    }}
                  >
                    <Box grow="Yes">
                      <Text as="h2" size="H4">
                        Adicionar usuário
                      </Text>
                    </Box>
                    <Box shrink="No">
                      <IconButton
                        aria-label="Fechar"
                        size="300"
                        radii="300"
                        onClick={closeAddUserModal}
                      >
                        <Icon src={Icons.Cross} />
                      </IconButton>
                    </Box>
                  </Header>
                  <Box className={AddUserModalBody} direction="Column" gap="500">
                    <Text size="T300" priority="400">
                      Abra a área para informar o ID Matrix do colega e iniciar uma conversa direta.
                    </Text>
                    <Box className={AddUserModalActions} gap="200" justifyContent="End">
                      <Button
                        variant="Secondary"
                        size="400"
                        radii="300"
                        onClick={closeAddUserModal}
                      >
                        <Text as="span" size="B400">
                          Cancelar
                        </Text>
                      </Button>
                      <Button
                        variant="Primary"
                        size="400"
                        radii="300"
                        onClick={openAddUserArea}
                        before={<Icon size="100" src={Icons.UserPlus} />}
                      >
                        <Text as="span" size="B400">
                          Adicionar usuário
                        </Text>
                      </Button>
                    </Box>
                  </Box>
                </Box>
              </Modal>
            </FocusTrap>
          </OverlayCenter>
        </Overlay>
      )}
    </>
  );
}
