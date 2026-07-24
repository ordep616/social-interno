import React, { ReactNode, useEffect, useMemo, useState } from 'react';
import { AutoDiscoveryInfoProvider } from '../../hooks/useAutoDiscoveryInfo';
import { AutoDiscoveryInfo, autoDiscovery } from '../../cs-api';
import { useClientConfig } from '../../hooks/useClientConfig';

type AutoDiscoveryProps = {
  baseUrl: string;
  children: ReactNode;
};
export function AutoDiscovery({ baseUrl, children }: AutoDiscoveryProps) {
  const clientConfig = useClientConfig();
  const configuredRtcFoci = clientConfig.matrixRTC?.rtcFoci;

  const withConfiguredRtcFoci = useMemo(
    () =>
      (info: AutoDiscoveryInfo): AutoDiscoveryInfo => {
        if (!configuredRtcFoci?.length || info['org.matrix.msc4143.rtc_foci']) {
          return info;
        }

        return {
          ...info,
          'org.matrix.msc4143.rtc_foci': configuredRtcFoci,
        };
      },
    [configuredRtcFoci]
  );

  const fallback: AutoDiscoveryInfo = useMemo(
    () =>
      withConfiguredRtcFoci({
        'm.homeserver': {
          base_url: baseUrl,
        },
      }),
    [baseUrl, withConfiguredRtcFoci]
  );

  const [info, setInfo] = useState<AutoDiscoveryInfo>(fallback);

  useEffect(() => {
    let disposed = false;

    setInfo(fallback);
    autoDiscovery(fetch, baseUrl).then(([, discovered]) => {
      if (!disposed && discovered) {
        setInfo(withConfiguredRtcFoci(discovered));
      }
    });

    return () => {
      disposed = true;
    };
  }, [baseUrl, fallback, withConfiguredRtcFoci]);

  return <AutoDiscoveryInfoProvider value={info}>{children}</AutoDiscoveryInfoProvider>;
}
