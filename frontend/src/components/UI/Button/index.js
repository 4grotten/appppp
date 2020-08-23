import * as React from 'react';
import * as classnames from 'classnames';
import './index.scss';

const Button = ({ label, type, className, ...other }) => (
  <button
    type={type || 'button'}
    className={classnames(    "button", className)}
    {...other}
  >
    <span className="button__label">{label}</span>
  </button>
)

export default Button;