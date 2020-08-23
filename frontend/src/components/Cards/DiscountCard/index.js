import React from 'react';
import * as classnames from 'classnames';
import {GearIcon} from '../../UI/Icons';
import './index.scss';

const DiscountCard = ({ card, clientStatus, onEditClick, name, isOwner }) => {
  if (!card) {return null;}
  const [showImage, setShow] = React.useState(true);
  const { percent } = card;

  return (
    <div className={classnames("discount-card", `discount-card-${card.type}`)}>
      {isOwner ? <GearIcon className="discount-card__settings" onClick={onEditClick} /> : <div />}
      {card.image && showImage && (
        <img
          className="discount-card__img"
          src={card.image.large}
          onError={() => setShow(false)}
          alt={card.image.name}
        />
      )}
      <span className="discount-card__amount">{`${percent}%`}</span>
      {name && <p className="discount-card__name f-600 f-17">{name}</p>}
      {clientStatus && clientStatus.total_spent < parseInt(card.limit) && (
        <div className="discount-card__overlay">
          <p className="discount-card__overlay-text f-17 f-600">Вам совсем осталось <br /> чуть-чуть до {percent} % скидки</p>
        </div>
      )}
    </div>
  );
};

export default DiscountCard;