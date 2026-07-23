import React, { useEffect, useMemo } from 'react';
import { Box, Header, Scroll, Spinner, Text, color } from 'folds';
import { Outlet, matchPath, useLocation, useNavigate, useParams } from 'react-router-dom';

import { AuthFooter } from './AuthFooter';
import * as css from './styles.css';
import {
  clientDefaultServer,
  clientDefaultServerName,
  useClientConfig,
} from '../../hooks/useClientConfig';
import { RESET_PASSWORD_PATH } from '../paths';
import { getLoginPath, getResetPasswordPath } from '../pathUtils';
import { AutoDiscoveryInfo } from '../../cs-api';
import { SpecVersionsLoader } from '../../components/SpecVersionsLoader';
import { SpecVersionsProvider } from '../../hooks/useSpecVersions';
import { AutoDiscoveryInfoProvider } from '../../hooks/useAutoDiscoveryInfo';
import { AuthFlowsLoader } from '../../components/AuthFlowsLoader';
import { AuthFlowsProvider } from '../../hooks/useAuthFlows';
import { AuthServerProvider } from '../../hooks/useAuthServer';
import WelcomeBackground from '../../../../public/res/background/betweenus-welcome.jpeg';

const currentAuthPath = (pathname: string): string => {
  if (matchPath(RESET_PASSWORD_PATH, pathname)) {
    return getResetPasswordPath();
  }
  return getLoginPath();
};

function AuthLayoutLoading({ message }: { message: string }) {
  return (
    <Box justifyContent="Center" alignItems="Center" gap="200">
      <Spinner size="100" variant="Secondary" />
      <Text align="Center" size="T300">
        {message}
      </Text>
    </Box>
  );
}

function AuthLayoutError({ message }: { message: string }) {
  return (
    <Box justifyContent="Center" alignItems="Center" gap="200">
      <Text align="Center" style={{ color: color.Critical.Main }} size="T300">
        {message}
      </Text>
    </Box>
  );
}

export function AuthLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const { server: urlEncodedServer } = useParams();

  const clientConfig = useClientConfig();
  const baseUrl = clientDefaultServer(clientConfig);
  const serverName = clientDefaultServerName(clientConfig);

  const autoDiscoveryInfo: AutoDiscoveryInfo = useMemo(
    () => ({
      'm.homeserver': {
        base_url: baseUrl,
      },
    }),
    [baseUrl]
  );

  useEffect(() => {
    if (urlEncodedServer) {
      navigate(currentAuthPath(location.pathname), { replace: true });
    }
  }, [urlEncodedServer, navigate, location]);

  return (
    <Scroll variant="Background" visibility="Hover" size="300" hideTrack>
      <Box
        className={css.AuthLayout}
        style={{ backgroundImage: `url(${WelcomeBackground})` }}
        direction="Column"
        alignItems="Center"
        justifyContent="SpaceBetween"
        gap="400"
      >
        <Box direction="Column" className={css.AuthCard}>
          <Header className={css.AuthHeader} size="600" variant="Surface">
            <Box grow="Yes" direction="Row" gap="300" alignItems="Center">
              <Text size="H3">Comunicação Interna</Text>
            </Box>
          </Header>
          <Box className={css.AuthCardContent} direction="Column">
            <AuthServerProvider value={serverName}>
              <AutoDiscoveryInfoProvider value={autoDiscoveryInfo}>
                <SpecVersionsLoader
                  baseUrl={baseUrl}
                  fallback={() => <AuthLayoutLoading message="Conectando ao homeserver..." />}
                  error={() => (
                    <AuthLayoutError message="Falha ao conectar. O homeserver está indisponível no momento ou não existe." />
                  )}
                >
                  {(specVersions) => (
                    <SpecVersionsProvider value={specVersions}>
                      <AuthFlowsLoader
                        fallback={() => (
                          <AuthLayoutLoading message="Carregando fluxo de autenticação..." />
                        )}
                        error={() => (
                          <AuthLayoutError message="Falha ao obter informações do fluxo de autenticação." />
                        )}
                      >
                        {(authFlows) => (
                          <AuthFlowsProvider value={authFlows}>
                            <Outlet />
                          </AuthFlowsProvider>
                        )}
                      </AuthFlowsLoader>
                    </SpecVersionsProvider>
                  )}
                </SpecVersionsLoader>
              </AutoDiscoveryInfoProvider>
            </AuthServerProvider>
          </Box>
        </Box>
        <AuthFooter />
      </Box>
    </Scroll>
  );
}
