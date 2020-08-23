import React from 'react';
import * as classnames from 'classnames';
import OrgAvatar from '../../UI/OrgAvatar';
import {getBadge, NOTIFICATION_TYPES} from './types';
import {Link} from 'react-router-dom';
import {prettyDate} from '../../../common/utils';
import Avatar from '../../UI/Avatar';
import './index.scss';

const NOT_REDIRECTABLE_TYPES = [
  NOTIFICATION_TYPES.decline_discount,
]

const NotificationCard = props => {
  const { card, className } = props;
  const { type, organization, extra_data} = card;
  if (!organization) { return null; }

  if (
    type === NOTIFICATION_TYPES.requested_partnership_recipient ||
    type === NOTIFICATION_TYPES.requested_partnership ||
    type === NOTIFICATION_TYPES.declined_partnership_recipient ||
    type === NOTIFICATION_TYPES.declined_partnership ||
    type === NOTIFICATION_TYPES.accepted_partnership_recipient ||
    type === NOTIFICATION_TYPES.accepted_partnership
  ) {
    return customPartnershipCard(props);
  }

  if (!NOT_REDIRECTABLE_TYPES.includes(type)) {
    let href = `/organizations/${card.organization.id}`;
    let content = defaultContent(card, (
      type === NOTIFICATION_TYPES.new_discount ||
      type === NOTIFICATION_TYPES.organization_message
    ));

    if (type === NOTIFICATION_TYPES.accepted_seller_discount) {
      href = `/organizations/${card.organization.id}/receipts/${extra_data.transaction_id}`;
    }

    if (type === NOTIFICATION_TYPES.accept_discount && extra_data) {
      href = `/receipts/${extra_data.transaction_id}?org=${card.organization.id}`;
    }

    if ((type === NOTIFICATION_TYPES.sent_message || type === NOTIFICATION_TYPES.organization_message) && extra_data) {
      if (extra_data.can_send_message) {
        href = `/organizations/${card.organization.id}/messages/`;
      } else {
        href = `/messages?org=${card.organization.id}`;
      }
    }

    if ((
      type === NOTIFICATION_TYPES.changed_position_as_owner ||
      type === NOTIFICATION_TYPES.recruit ||
      type === NOTIFICATION_TYPES.changed_position
    ) && extra_data && extra_data.can_edit_organization) {
      href = `/organizations/${card.organization.id}/employees/${extra_data.membership_id}`;
    }

    if (type === NOTIFICATION_TYPES.new_organization) {
      content = newOrganizationContent(card);
    }

    return (
      <Link to={href} className={classnames("notification-card", className)}>
        {defaultAvatar(card)}
        {content}
      </Link>
    )
  }

  return (
    <div className={classnames("notification-card", className)}>
      {defaultAvatar(card)}
      {defaultContent(card)}
    </div>
  );
};

export default NotificationCard;

const defaultAvatar = (card) => (
  <div className="notification-card__avatar">
    <OrgAvatar
      src={(card.organization && card.organization.image && card.organization.image.medium) || ''}
      alt={(card.organization && card.organization.title) || ''}
      size={60}
    />
    <div className="notification-card__badge">{getBadge(card)}</div>
  </div>
)

const defaultContent = (card, disableSender) => (
  <div className="notification-card__content">
    <h6 className="notification-card__title f-15 tl">{card.title}</h6>
    <p className="notification-card__title f-15 f-600 tl">{card.organization.title}</p>
    <p className="notification-card__desc f-12 tl">{card.description}</p>
    {!disableSender && getSender(card.sender)}
    <p className="notification-card__time f-12 tl">{prettyDate(card.created_at)}</p>
  </div>
)

const getSender = sender => sender ? (
    <div className="notification-card__sender">
      <Avatar
        src={sender.avatar && sender.avatar.medium}
        alt={sender.full_name}
        size={24}
      />
      <span className="notification-card__sender-name f-12 tl">{sender.full_name}</span>
    </div>
  ) : null;

const newOrganizationContent = (card) => (
  <div className="notification-card__content">
    <h6 className="notification-card__title f-15 tl">{card.title}</h6>
    <p className="notification-card__title f-15 f-600 tl">{card.organization.title}</p>
    <p className="notification-card__desc f-12 tl">{card.organization.address}</p>
  </div>
)

const customPartnershipCard = ({ card, className, onAcceptPartnership, onRejectPartnership }) => {
  let status = '';
  if (card.type === NOTIFICATION_TYPES.requested_partnership) { status = 'В ожидании'; }
  if (card.type === NOTIFICATION_TYPES.accepted_partnership) { status = 'Принят'; }
  if (card.type === NOTIFICATION_TYPES.declined_partnership_recipient) { status = 'Вы отклонили'; }
  if (card.type === NOTIFICATION_TYPES.accepted_partnership_recipient) { status = 'Вы приняли'; }
  if (card.type === NOTIFICATION_TYPES.declined_partnership) { status = 'Отклонен'; }

  const content = (
    <React.Fragment>
      {defaultAvatar(card)}
      <div className="notification-card__content">
        <h6 className="notification-card__title f-15">{card.title}</h6>
        {card.description && <p className="notification-card__desc f-12 tl">{card.description}</p>}
        {getSender(card.sender)}
        <p className="notification-card__time f-12 tl">{prettyDate(card.created_at)}</p>
        <div className="notification-card__partnerships">
          {card.type === NOTIFICATION_TYPES.requested_partnership_recipient ? (
            <React.Fragment>
              <button className="notification-card__partnerships-accept f-14 f-500" onClick={() => {
                onAcceptPartnership(card.extra_data.partnership_id, `/organizations/${card.organization.id}/partners/${card.extra_data.partnership_id}`)
              }}>Принять</button>
              <button className="notification-card__partnerships-decline f-14 f-500" onClick={() => {
                onRejectPartnership(card.extra_data.partnership_id);
              }}>
                Отклонить
              </button>
            </React.Fragment>
          ) : <div className={classnames("notification-card__partnerships-status", "f-14 f-500", `notification-card__partnerships-${card.type}`)}>{status}</div>}
        </div>
      </div>
    </React.Fragment>
  )

  if (card.type === NOTIFICATION_TYPES.accepted_partnership_recipient || card.type === NOTIFICATION_TYPES.accepted_partnership) {
    return (
      <Link to={`/organizations/${card.organization.id}/partners/${card.extra_data.partnership_id}`} className={classnames("notification-card", className)}>
        {content}
      </Link>
    )
  }

  return (
    <div className={classnames("notification-card", className)}>
      {content}
    </div>
  )
}