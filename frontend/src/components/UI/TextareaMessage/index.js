import React from 'react';
import * as classnames from 'classnames';
import TextareaAutosize from 'react-textarea-autosize';
import './index.scss';

const MessageTextarea = ({ value, onChange, placeholder, error, limit = 800, className }) => {
  return (
    <div className={classnames("message-textarea__wrap", className)} >
      <TextareaAutosize
        name="text"
        placeholder={placeholder}
        value={value}
        onChange={onChange}
        minRows={10}
        className={classnames("message-textarea f-15", error && "message-textarea__error")}
      />
      <div className="message-textarea__counter f-14">
        <span className={classnames(value.length > limit && 'message-textarea__counter-error')}>{value.length}</span>/{limit}
      </div>
      {error && <div className={classnames("message-textarea__error-text f-14")}>{error}</div>}
    </div>
  );
};

export default MessageTextarea;