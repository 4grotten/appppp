import React from 'react';
import * as classnames from 'classnames';
import TextareaAutosize from 'react-textarea-autosize';
import './index.scss';

const TextareaField = ({ value, error, onChange, placeholder, name, className}) => (
 <div>
   <TextareaAutosize
     name={name}
     placeholder={placeholder}
     value={value}
     maxRows={3}
     onChange={onChange}
     className={classnames("textarea-field f-14", error && "textarea-field__error", className)}
   />
   {error && <div className={classnames("textarea-field__error-text")}>{error}</div>}
 </div>
);

export default TextareaField;