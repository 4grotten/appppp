import React from 'react';
import * as classnames from 'classnames';
import {Link} from 'react-router-dom';
import OrgAvatar from '../../UI/OrgAvatar';
import './index.scss';

const OrganizationCard = ({ id, image, title, description, redirect, children, className }) => (
  <Link
    to={redirect ? redirect() : `/organizations/${id}`}
    className={classnames("organization-card__wrap", className)}
  >
    <div className="organization-card">
      <OrgAvatar
        src={image}
        alt={title}
        size={40}
        borderRadius={'11px'}
        className="organization-card__image"
      />
      <div className="organization-card__right">
        <p className="organization-card__title f-15 tl">{title}</p>
        {description && <p className="organization-card__desc f-12 tl">{description}</p>}
        {children}
      </div>
    </div>
  </Link>
);

export default OrganizationCard;