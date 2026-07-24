import React, { ReactNode, useEffect, useMemo, useState } from 'react';
import { AutoDiscoveryInfoProvider } from '../../hooks/useAutoDiscoveryInfo';
import { AutoDiscoveryInfo, autoDiscovery } from '../../cs-api';

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

  const [info, setInfo] = useState<AutoDiscoveryInfo>(fallback);

  useEffect(() => {
    let disposed = false;

    setInfo(fallback);
    autoDiscovery(fetch, baseUrl).then(([, discovered]) => {
      if (!disposed && discovered) {
        setInfo(discovered);
      }
    });

    return () => {
      disposed = true;
    };
  }, [baseUrl, fallback]);

  return <AutoDiscoveryInfoProvider value={info}>{children}</AutoDiscoveryInfoProvider>;
}
