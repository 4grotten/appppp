import React from 'react';
import * as classnames from 'classnames';
import Avatar from '../../UI/Avatar';
import PropTypes from 'prop-types';
import './index.scss';

const UserCard = ({ avatar, fullname, description, smallSize, withBorder, className }) => {
  return (
    <div className={classnames("user-card", className)}>
      <Avatar
        src={avatar && avatar.medium}
        alt={fullname}
        size={smallSize ? 40 : 48}
        withBorder={withBorder}
        className="user-card__avatar"
      />

      <div className="user-card__content">
        <h6 className={classnames("f-500 tl", smallSize ? "f-15" : "f-16")}>{fullname}</h6>
        {description && <p className={classnames("user-card__content-desc f-500 tl", smallSize ? "f-12" : "f-13")}>{description}</p>}
      </div>
    </div>
  );
};

UserCard.defaultProps = {
  fullname: 'User',
  description: '',
}

UserCard.propTypes = {
  avatar: PropTypes.object,
  fullname: PropTypes.string,
  description: PropTypes.string,
  withBorder: PropTypes.bool,
  className: PropTypes.string,
};

export default UserCard;