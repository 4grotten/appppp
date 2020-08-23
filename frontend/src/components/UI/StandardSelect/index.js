import React from 'react';
import * as classnames from 'classnames';
import {DEFAULT_EMPTY} from '../../../common/constants';
import {ArrowRight} from '../Icons';
import './index.scss';

const StandardSelect = ({ label, value, name, options, className, onChange }) => {
  return (
    <div className={classnames("standard-select", className)}>
      <label htmlFor={name} className="standard-select__label f-14">{label}</label>
      <div className="standard-select__container">
        <select
          name={name}
          onChange={onChange}
          value={value}
          className="standard-select__select"
        >
          <option value={DEFAULT_EMPTY}>Без скидки</option>
          {options.map(card => (
            <option key={card.value} value={card.value}>{card.label}</option>
          ))}
        </select>
        <ArrowRight className="standard-select__arrow" />
      </div>
    </div>
  );
};

export default StandardSelect;