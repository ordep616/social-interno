import { createContext, useContext } from 'react';
import { trimTrailingSlash } from '../utils/common';

export type HashRouterConfig = {
  enabled?: boolean;
  basename?: string;
};

export type ClientConfig = {
  defaultHomeserver?: number;
  homeserverList?: string[];
  allowCustomHomeservers?: boolean;

  featuredCommunities?: {
    openAsDefault?: boolean;
    spaces?: string[];
    rooms?: string[];
    servers?: string[];
  };

  hashRouter?: HashRouterConfig;
};

const ClientConfigContext = createContext<ClientConfig | null>(null);

export const ClientConfigProvider = ClientConfigContext.Provider;

export function useClientConfig(): ClientConfig {
  const config = useContext(ClientConfigContext);
  if (!config) throw new Error('Client config are not provided!');
  return config;
}

export const normalizeHomeserverUrl = (server: string): string => trimTrailingSlash(server);

export const clientDefaultServer = (clientConfig: ClientConfig): string =>
  normalizeHomeserverUrl(
    clientConfig.homeserverList?.[clientConfig.defaultHomeserver ?? 0] ?? 'http://localhost:8008'
  );

export const clientDefaultServerName = (clientConfig: ClientConfig): string => {
  const server = clientDefaultServer(clientConfig);
  try {
    return new URL(server).host;
  } catch {
    return server;
  }
};

export const clientAllowedServer = (clientConfig: ClientConfig, server: string): boolean => {
  const { homeserverList } = clientConfig;

  const normalizedServer = normalizeHomeserverUrl(server);
  return homeserverList?.map(normalizeHomeserverUrl).includes(normalizedServer) === true;
};
