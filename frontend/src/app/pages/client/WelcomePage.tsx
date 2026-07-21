import React from 'react';
import { Text } from 'folds';
import { Page } from '../../components/page';
import * as css from './WelcomePage.css';
import WelcomeBackground from '../../../../public/res/background/betweenus-welcome.jpeg';
import AppLogo from '../../../../public/res/logo/company-logo.png';
import ExplorerNetLogo from '../../../../public/res/logo/explorernet-logo.png';

export function WelcomePage() {
  return (
    <Page className={css.WelcomePageRoot} style={{ backgroundImage: `url(${WelcomeBackground})` }}>
      <Text as="h1" className={css.ScreenReaderOnly}>
        Bem-vindo ao Betweenus
      </Text>
      <div className={css.CenterStage} aria-hidden="true">
        <div className={css.CenterLockup}>
          <img className={css.AppLogo} width="184" height="184" src={AppLogo} alt="" />
          <Text className={css.WelcomeTitle} as="p">
            Bem-vindo ao Betweenus
          </Text>
        </div>
      </div>
      <img className={css.ExplorerNetLogo} src={ExplorerNetLogo} alt="" aria-hidden="true" />
    </Page>
  );
}
