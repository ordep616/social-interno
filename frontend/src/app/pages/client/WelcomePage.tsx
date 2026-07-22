import React, { useState } from 'react';
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
  Scroll,
  Text,
  config,
} from 'folds';
import FocusTrap from 'focus-trap-react';
import { Page, PageHeroSection } from '../../components/page';
import { stopPropagation } from '../../utils/keyboard';
import { CreateChat } from '../../features/create-chat';
import {
  AddUserModal,
  AddUserModalBody,
  CenterContrast,
  WelcomeLogo,
  NeonChatButton,
  NeonChatButtonText,
  WelcomePageRoot,
  WelcomeTitle,
} from './WelcomePage.css';
import WelcomeBackground from '../../../../public/res/background/betweenus-welcome.jpeg';
import WelcomeLogoImage from '../../../../public/res/logo/welcome-logo.png';

export function WelcomePage() {
  const [addUserModal, setAddUserModal] = useState(false);

  const closeAddUserModal = () => setAddUserModal(false);

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
                className={WelcomeLogo}
                width="160"
                height="160"
                src={WelcomeLogoImage}
                alt="Logo Betweenus"
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
              <Modal className={AddUserModal} size="400" variant="Background" flexHeight>
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
                  <Scroll size="300" hideTrack>
                    <Box className={AddUserModalBody} direction="Column" gap="500">
                      <Text size="T300" priority="400">
                        Informe o ID Matrix do colega para iniciar uma conversa direta.
                      </Text>
                      <CreateChat />
                    </Box>
                  </Scroll>
                </Box>
              </Modal>
            </FocusTrap>
          </OverlayCenter>
        </Overlay>
      )}
    </>
  );
}
