import React from 'react';
import PropTypes from 'prop-types';
import * as classnames from 'classnames';
import './index.scss';

const OrgAvatar = ({ src, alt, size, borderRadius, className }) => {
  const style = {
    width: size,
    minWidth: size,
    height: size,
    minHeight: size,
    borderRadius,
  }

  return (
    <div className={classnames("org-avatar", className)} style={style}>
      <img
        className="org-avatar__image"
        src={src}
        alt={alt}
      />
    </div>
  );
};

OrgAvatar.defaultProps = {
  src: '',
  alt: 'Organization Logo',
  size: 72,
  borderRadius: '12px',
}

OrgAvatar.propTypes = {
  src: PropTypes.string.isRequired,
  alt: PropTypes.string.isRequired,
  size: PropTypes.number,
  className: PropTypes.string,
};

export default OrgAvatar;