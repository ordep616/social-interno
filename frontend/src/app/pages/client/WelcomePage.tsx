import React from 'react';
import { Box, Text, config } from 'folds';
import { Page, PageHeroSection } from '../../components/page';
import AppLogo from '../../../../public/res/logo/company-logo.png';
import ExplorerNetLogo from '../../../../public/res/logo/explorernet-logo.png';

export function WelcomePage() {
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
