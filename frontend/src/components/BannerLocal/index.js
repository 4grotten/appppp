import React from 'react';
import OrgAvatar from '../UI/OrgAvatar';
import {getRandomElementFromArray} from '../../common/utils';
import {Link} from 'react-router-dom';
import './index.scss';

const MESSAGES = [
  (title, type, discount) => `Теперь вы можете посещать ${type} ${title} со скидкой до ${discount}%`,
  (title, type, discount) => `Специально для Вас ${type} ${title} подготовила скидки до ${discount}%`,
  (title, type, discount) => `${type} ${title} дарит скидку до ${discount}%`,
  (title, type, discount) => `Уже сегодня ${type} ${title} подарит Вам скидку до ${discount}%`,
  (title, type, discount) => `Раскажите всем ${type} ${title} дарит теперь скидки до ${discount}%`,
]

const MAX_LENGTH = 19;

const getBannerText = (title, type = '', discount) => {
  let shortenTitle = title;
  if (title.length > MAX_LENGTH) {
    shortenTitle = title.slice(0, MAX_LENGTH) + '...';
  }
  return getRandomElementFromArray(MESSAGES)(shortenTitle, type, discount);
}

const BannerLocal = ({ banner, background }) => {
  const { id, image, max_discount, title, types } = banner;

  return (
    <Link className="banner-local" style={{ background }} to={`/organizations/${id}`}>
      <div className="banner-local__inner">
        <OrgAvatar
          src={image && image.medium}
          alt={title}
          size={60}
          className="banner-local__left"
        />
        <div className="banner-local__right">
          <h4 className="banner-local__title f-20 f-600 tl">{title}</h4>
          <p className="banner-local__desc f-14 f-600">{getBannerText(title, types[0] && types[0].title, max_discount)}</p>
        </div>
      </div>
    </Link>
  );
};

export default BannerLocal;