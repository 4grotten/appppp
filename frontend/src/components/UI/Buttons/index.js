import React from 'react';
import * as classnames from 'classnames';
import './index.scss';

export const StandardButton = ({ label, onClick, className, ...other }) => (
  <button type="button" onClick={onClick} className={classnames("standard-button", className)} {...other} >
    <span className="standard-button__label f-600 f-14">{label}</span>
  </button>
);