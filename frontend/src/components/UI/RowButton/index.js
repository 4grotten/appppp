import React from 'react';
import * as classnames from 'classnames';
import {ArrowRight} from '../Icons';
import {Link} from 'react-router-dom';
import './index.scss';

export const ROW_BUTTON_TYPES = {
  button: 'button',
  link: 'link'
}

const RowButton = ({ label, children, showArrow = true, ...other }) => (
  <Wrapper { ...other } >
    <div className="row-button__left dfc">
      {children}
      <span className="row-button__label">{label}</span>
    </div>
    {showArrow && <ArrowRight />}
  </Wrapper>
);

export default RowButton;


const Wrapper = ({ type = ROW_BUTTON_TYPES.button, onClick, to, className, children }) => (
  type === ROW_BUTTON_TYPES.button
    ? (
      <button type="button" onClick={onClick} className={classnames("row-button row", className)}>
        {children}
      </button>
    ) : (
      <Link to={to} className={classnames("row-button row", className)} >
        {children}
      </Link>
    )
)