import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Box, Button, Text, config } from 'folds';
import { Page, PageHeroSection } from '../../components/page';
import { getDirectCreatePath } from '../pathUtils';
import {
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

  return (
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
              onClick={() => navigate(getDirectCreatePath())}
            >
              <Text className={NeonChatButtonText} as="span" size="B400" truncate>
                Comece a conversar agora!
              </Text>
            </Button>
          </Box>
        </PageHeroSection>
      </Box>
    </Page>
  );
}
