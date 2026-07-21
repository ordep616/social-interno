import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Box, Button, Text, config } from 'folds';
import { Page, PageHeroSection } from '../../components/page';
import { getDirectCreatePath } from '../pathUtils';
import { NeonChatButton, NeonChatButtonText } from './WelcomePage.css';
import AppLogo from '../../../../public/res/logo/company-logo.png';
import ExplorerNetLogo from '../../../../public/res/logo/explorernet-logo.png';

export function WelcomePage() {
  const navigate = useNavigate();

  return (
    <Page style={{ position: 'relative', overflow: 'hidden' }}>
      <Box
        grow="Yes"
        style={{ padding: config.space.S700 }}
        alignItems="Center"
        justifyContent="Center"
      >
        <PageHeroSection>
          <Box direction="Column" alignItems="Center" gap="500">
            <img
              width="160"
              height="160"
              src={AppLogo}
              alt="Betweenus logo"
              style={{ borderRadius: '50%', objectFit: 'cover' }}
            />
            <Text as="h1" align="Center" size="H2">
              Bem-Vindo ao Betweenus
            </Text>
            <Button
              className={NeonChatButton}
              size="500"
              radii="300"
              onClick={() => navigate(getDirectCreatePath())}
            >
              <Text className={NeonChatButtonText} as="span" size="B400" truncate>
                Comece a conversar agora!
              </Text>
            </Button>
          </Box>
        </PageHeroSection>
      </Box>
      <img
        width="260"
        src={ExplorerNetLogo}
        alt="ExplorerNet"
        style={{
          position: 'absolute',
          right: config.space.S500,
          bottom: config.space.S500,
          width: 'clamp(180px, 28vw, 320px)',
          height: 'auto',
        }}
      />
    </Page>
  );
}
