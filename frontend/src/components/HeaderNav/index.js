import React from 'react';
import * as classnames from 'classnames';
import {NavLink} from 'react-router-dom';
import './index.scss';

export const HeaderNav = ({ routes, className }) => (
  <div className={classnames("header-nav", className)}>
    {routes.map(route => (
      <NavLink
        to={route.path}
        key={route.label}
        route={route.label}
        className="header-nav__item f-16 f-500"
        activeClassName="header-nav__item-active"
      >
        {route.label}
      </NavLink>
    ))}
  </div>
);