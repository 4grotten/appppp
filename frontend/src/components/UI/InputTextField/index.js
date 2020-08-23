import * as React from 'react';
import * as classnames from 'classnames';
import {ArrowRight, ClipboardIcon, RemoveIcon} from '../Icons';
import './index.scss';

export const InputTextField = props => {
  const {label, name, value, onClick, onChange, className, onCopy, error, onAdd, onRemove, showArrow, onMap, ...other} = props;
  return (
    <div className={classnames("input-text-field", error && "input-text-field_error", className)}>
      <div className="input-text-field__input-group">
        <input
          type="text"
          id={name}
          name={name}
          value={value}
          style={{paddingRight: (onRemove || onCopy) ? '60px' : '0'}}
          placeholder=' '
          onClick={onClick}
          onChange={onChange}
          className={classnames("input-text-field__input", value && "input-text-field__input-filled")}
          {...other}
        />
        <label className="input-text-field__label" htmlFor={name}>{label}</label>
        {(onRemove || onCopy || showArrow || onMap) && (
          <div className="input-text-field__tools">
            {onCopy && <ClipboardIcon text={value} className="input-text-field__tools-copy" />}
            {onRemove && <RemoveIcon onClick={onRemove} className="input-text-field__tools-remove"  />}
            {showArrow && <ArrowRight />}
            {onMap && <span className="input-text-field__map f-14" onClick={onMap}>на карте</span>}
          </div>
        )}
      </div>
      <div className={classnames("input-text-field__error", error && "input-text-field__error_visible")}>{error}</div>
    </div>
  )
};