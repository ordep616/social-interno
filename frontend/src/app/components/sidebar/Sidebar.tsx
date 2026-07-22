import classNames from 'classnames';
import { as } from 'folds';
import React from 'react';
import * as css from './Sidebar.css';

export const Sidebar = as<'div'>(({ as: AsSidebar = 'div', className, ...props }, ref) => (
  <AsSidebar className={classNames(css.Sidebar, className)} {...props} ref={ref} />
));

export const SidebarResizeHandle = as<'div'>(
  ({ as: AsSidebarResizeHandle = 'div', className, ...props }, ref) => (
    <AsSidebarResizeHandle
      className={classNames(css.SidebarResizeHandle, className)}
      {...props}
      ref={ref}
    />
  )
);
