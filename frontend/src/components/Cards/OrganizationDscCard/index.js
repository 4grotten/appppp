import React from 'react';
import * as classnames from 'classnames';
import AvatarSquare from '../../UI/AvatarSquare';
import {Link} from 'react-router-dom';
import './index.scss';

const OrganizationDscCard = ({ organization, className }) => {
  if (!organization) { return null; }
  const { id, title, types, image, discounts } = organization;

  return (
    <Link to={`/organizations/${id}`} className={classnames("organization-dsc-card", className)}>
      <AvatarSquare
        className="organization-dsc-card__avatar"
        src={image && image.medium}
        alt={title}
      />

      <div className="organization-dsc-card__right">
        <p className="f-12 tl">{types[0] && types[0].title}</p>
        <h5 className="organization-dsc-card__title f-18 f-400 tl">{title}</h5>
        {discounts && !!discounts.length ? (
          <ul className="organization-dsc-card__discounts">
            {discounts.slice(-3).map(discount => (
              <li
                key={discount}
                className="organization-dsc-card__discount f-14 f-600">
                {`${discount}%`}
              </li>
            ))}
          </ul>
        ) : <div className="organization-dsc-card__discount f-14 f-600">Нет скидок</div>}
      </div>
    </Link>
  );
};

export default OrganizationDscCard;