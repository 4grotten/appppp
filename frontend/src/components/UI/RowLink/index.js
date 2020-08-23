import React from 'react';
import * as classnames from 'classnames';
import {Link} from 'react-router-dom';
import {ArrowRight} from '../Icons';
import './index.scss';

const RowLink = ({ to, children, className, label }) => {
  return (
    <Link className={classnames("row-link", className)} to={to}>
      <div className="row-link__left">
        {children}
        <span className="row-link__label">{label}</span>
      </div>
      <ArrowRight />
    </Link>
  );
};

export default RowLink;