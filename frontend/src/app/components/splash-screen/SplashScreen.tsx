import { Box, Text } from 'folds';
import React, { ReactNode } from 'react';
import classNames from 'classnames';
import * as patternsCSS from '../../styles/Patterns.css';
import * as css from './SplashScreen.css';
import AppLogo from '../../../../public/res/logo/company-logo.png';

type SplashScreenProps = {
  children: ReactNode;
};
export function SplashScreen({ children }: SplashScreenProps) {
  return (
    <Box
      className={classNames(css.SplashScreen, patternsCSS.BackgroundDotPattern)}
      direction="Column"
    >
      {children}
      <Box
        className={css.SplashScreenFooter}
        shrink="No"
        direction="Column"
        gap="200"
        alignItems="Center"
        justifyContent="Center"
      >
        <img
          width="64"
          height="64"
          src={AppLogo}
          alt="Exp logo"
          style={{ borderRadius: '50%', objectFit: 'cover' }}
        />
        <Text size="H2" align="Center">
          Exp
        </Text>
      </Box>
    </Box>
  );
}
