import React from 'react';
import * as classnames from 'classnames';
import {DoneIcon} from '../Icons';
import './index.scss'

const Option = ({ label, active, onSelect, className }) => (
  <div className={classnames("option", active && "option-active", className)} onClick={onSelect} >
    <p className="f-16 tl">{label}</p>
    <DoneIcon />
  </div>
);

export default Option;