import * as React from 'react';
import * as classnames from 'classnames';
import {ArrowRight} from '../Icons';
import './index.scss';

export const CurrencyInput = props => {
  const {label, name, value, className, onClick, error, ...other} = props;
  return (
    <div className={classnames("currency-input", error && "currency-input_error", className)}>
      <div className="currency-input__input-group" onClick={onClick} >
        {value && (
          <div className="currency-input__flag" >
            <img src={value.flag} alt={value.name} />
          </div>
        )}
        <input
          type="text"
          id={name}
          name={name}
          value={value && value.currency && value.currency.name || ''}
          placeholder=' '
          onChange={() => null}
          className={classnames("currency-input__input", value && "currency-input__input-filled")}
          {...other}
        />
        <label className="currency-input__label" htmlFor={name}>{label}</label>
        <ArrowRight className="currency-input__arrow" />
      </div>
      <div className={classnames("currency-input__error", error && "currency-input__error_visible")}>{error}</div>
    </div>
  )
};