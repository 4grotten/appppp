import * as React from 'react';
import * as classnames from 'classnames';
import './index.scss';

const AvatarSquare = ({ src, alt, className, size = 60 }) => (
  <div className={classnames("avatar-square__container", className)} style={{
    width: size, height: size, maxWidth: size, maxHeight: size, minWidth: size, minHeight: size
  }}>
    <img
      src={src}
      alt={alt || 'Organization'}
      className="avatar-square__image"
    />
  </div>
)

export default AvatarSquare