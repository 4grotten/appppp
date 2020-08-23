import React from 'react';
import * as classnames from 'classnames';
import ToggleSwitch from '../ToggleSwitch';
import './index.scss';

const RowToggle = ({ label, className, ...other }) => (
  <div className={classnames("row-toggle row", className)}>
    <p className="row-toggle__label f-17">{label}</p>
    <ToggleSwitch {...other} />
  </div>
);

export default RowToggle;