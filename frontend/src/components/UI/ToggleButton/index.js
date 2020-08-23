import React from 'react';
import * as classnames from 'classnames';
import './index.scss';

const ToggleButton = ({ label, toggled, className, onClick }) => {
  return (
    <button type="button" onClick={onClick} className={classnames("toggle-button", toggled && "toggle-button__active", className)} >
      <span className="toggle-button__label f-600">{label}</span>
      <svg width="10" height="6" viewBox="0 0 10 6" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M1.45832 0.691051C1.06676 0.384877 0.501131 0.454099 0.194957 0.845663C-0.111217 1.23723 -0.0419953 1.80286 0.349569 2.10903L4.44621 5.3123C4.77182 5.5669 5.22898 5.56699 5.55468 5.31252L9.65465 2.10925C10.0463 1.80323 10.1158 1.23763 9.80976 0.845942C9.50374 0.454257 8.93814 0.384813 8.54645 0.690833L5.00081 3.46101L1.45832 0.691051Z" fill="#818C99"/>
      </svg>
    </button>
  );
};

export default ToggleButton;