import React from 'react';
import * as classnames from 'classnames';
import Select from 'react-select';
import {singleValueSelect} from '../../../assets/styles/select';
import './index.scss';

const SelectField = ({ name, label, options, onChange, isDisabled, isLoading, isClearable, isSearchable, className }) => (
  <div className={classnames("select-field", className)}>
    <label htmlFor={name} className="select-field__label f-14">{label}</label>
    <Select
      className="select-field__select"
      classNamePrefix="select"
      defaultValue={options[0]}
      isDisabled={!!isDisabled}
      isLoading={isLoading}
      isClearable={!!isClearable}
      isSearchable={!!isSearchable}
      onChange={onChange}
      styles={singleValueSelect}
      name={name}
      options={options}
    />
    </div>
)

export default SelectField;