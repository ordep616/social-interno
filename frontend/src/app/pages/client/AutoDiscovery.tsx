import React, { ReactNode, useMemo } from 'react';
import { AutoDiscoveryInfoProvider } from '../../hooks/useAutoDiscoveryInfo';
import { AutoDiscoveryInfo } from '../../cs-api';

type AutoDiscoveryProps = {
  baseUrl: string;
  children: ReactNode;
};
export function AutoDiscovery({ baseUrl, children }: AutoDiscoveryProps) {
  const fallback: AutoDiscoveryInfo = useMemo(
    () => ({
      'm.homeserver': {
        base_url: baseUrl,
      },
    }),
    [baseUrl]
  );

  return <AutoDiscoveryInfoProvider value={fallback}>{children}</AutoDiscoveryInfoProvider>;
}
