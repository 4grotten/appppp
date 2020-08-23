import React from 'react';
import * as classnames from 'classnames';
import OrgAvatar from '../UI/OrgAvatar';
import {shortenNumber} from '../../common/helpers';
import {Link} from 'react-router-dom';
import './index.scss';

const OrganizationHeader = ({ id, title, image, types, subscribers, className }) => (
  <Link className={classnames("organization-header", className)} to={`/organizations/${id}/followers`} >
    <OrgAvatar
      src={image && image.large}
      alt={title}
      className="organization-header__left"
    />
    <div className="organization-header__right">
      <p className="organization-header__type f-12 tl">{types[0] && types[0].title || 'Вид организации'}</p>
      <h1 className="organization-header__title f-20 tl f-600">{title || 'Название организации'}</h1>
      {(subscribers === 0 || subscribers) && <p className="organization-header__subscribers f-14">Подписчиков: <b>{shortenNumber(subscribers)}</b></p>}
    </div>
  </Link>
);

export default OrganizationHeader;