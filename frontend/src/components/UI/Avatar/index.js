import * as React from 'react';
import * as classnames from 'classnames';
import {GENDER} from '../../../common/constants';
import {FemaleAvatar, MaleAvatar} from '../Icons';
import PropTypes from 'prop-types';
import './index.scss';

const Avatar = ({ src, alt, size, gender, error, withBorder, className }) => {
  const [loadError, setError] = React.useState(false);

  return (
    <div
      className={classnames("avatar__container", error && "avatar__error", withBorder && "avatar__bordered", className)}
      style={{ width: size, height: size, maxWidth: size, maxHeight: size, minWidth: size, minHeight: size}}
    >
      {src && !loadError ? (
        <img
          src={src}
          alt={alt}
          onError={() => setError(true)}
          className="avatar__image"
        />
      ) : gender === GENDER.female  ? <FemaleAvatar className="avatar__image" /> : <MaleAvatar className="avatar__image" />}
    </div>
  )
}

Avatar.defaultProps = {
  src: '',
  alt: 'Avatar',
  size: 132,
}

Avatar.propTypes = {
  src: PropTypes.string,
  alt: PropTypes.string,
  size: PropTypes.number,
  gender: PropTypes.string,
  className: PropTypes.string,
};

export default Avatar