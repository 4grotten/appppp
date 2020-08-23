import React from 'react';
import * as classnames from 'classnames';
import './index.scss';

const EmptyBox = ({ renderIcon, title, description, className }) => {
  return (
    <div className={classnames("empty-box__wrap", className)}>
      <div className="empty-box">
        {renderIcon && renderIcon()}
        {title && <p className="empty-box__title f-16 f-600">{title}</p>}
        {description && <p className="empty-box__desc f-14">{description}</p>}
      </div>
    </div>
  );
};

export default EmptyBox;