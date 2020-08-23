import React from 'react';
import * as classnames from 'classnames';
import OrgAvatar from '../../UI/OrgAvatar';
import {Link} from 'react-router-dom';
import {prettyDate} from '../../../common/utils';
import './index.scss';

const PartnershipCard = props => {
  const { partner, isAccepted, to, className } = props;
  if (!partner) { return null; }
  return isAccepted ? (
    <Link to={to} className={classnames("partner-card__wrap", className)}>
      {getContent(props)}
    </Link>
  ) : (
    <div className={classnames("partner-card__wrap", className)}>
      {getContent(props)}
    </div>
  )
};

export default PartnershipCard;

const getContent = ({ partner, isAccepted, isIncoming, onAcceptPartnership, onRejectPartnership }) => {
  const { title, image, address, partners, types, latest_transaction_time } = partner;
  return (
    <div className="partner-card">
      <OrgAvatar
        src={image && image.medium}
        alt={title + 'Logo'}
        className="partner-card__logo"
      />

      <div className="partner-card__right">
        <div className="partner-card__type-block row">
          <p className="partner-card__type f-12 f-500 tl">{(types[0] && types[0].title) || 'Фирменный магазин'}</p>
          {latest_transaction_time && <div className="partner-card__time f-11 f-500">{prettyDate(latest_transaction_time)}</div>}
        </div>
        <h4 className="partner-card__title f-16 tl">{title}</h4>
        <p className="partner-card__address f-12 tl">{address || '155 просп. Чуй. Бишкек'}</p>

        {!!partners.count && (
          <div className="partner-card__bottom">
            <div className="partner-card__group">
              {partners.list.map(partner => (
                <div key={partner.id} className="partner-card__group-image">
                  <img
                    src={partner.image && partner.image.small}
                    alt={partner.title}
                  />
                </div>
              ))}
            </div>

            <div className="partner-card__partners f-11">{partners.count} партнеров</div>
          </div>
        )}

        <div className="org-partners-page__item-buttons">
          {!isAccepted && !isIncoming && (
            <div className="org-partners-page__item-pending">В ожидании</div>
          )}

          {isIncoming && !isAccepted && (
            <React.Fragment>
              <button className="org-partners-page__item-accept f-14 f-500" onClick={onAcceptPartnership}>Принять</button>
              <button className="org-partners-page__item-decline f-14 f-500" onClick={onRejectPartnership}>Отклонить</button>
            </React.Fragment>
          )}
        </div>
      </div>
    </div>
  )
}