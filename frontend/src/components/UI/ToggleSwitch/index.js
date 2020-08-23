import React from 'react';
import './index.scss';

const ToggleSwitch = ({ checked, name, onChange }) => {
  return (
    <label className="toggle-switch" htmlFor={name}>
      <input type="checkbox" name={name} id={name} className="toggle-switch__input" onChange={onChange} checked={checked} />
      <span className="toggle-switch__slider toggle-switch__slider-round" />
    </label>
  );
};

export default ToggleSwitch;