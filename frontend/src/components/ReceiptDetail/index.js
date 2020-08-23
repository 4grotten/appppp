import React from 'react';
import * as classnames from 'classnames';
import Avatar from '../UI/Avatar';
import * as moment from 'moment';
import {DATE_FORMAT_DD_MM_YYYY_HH_MM} from '../../common/constants';
import {Link} from 'react-router-dom';
import Button from '../UI/Button';
import OrgAvatar from '../UI/OrgAvatar';
import './index.scss';

const ReceiptDetail = ({ receipt, showOrganization, children, viewProceederReceipts, onRemove, isRemoving, organizationID, className }) => {
  if (!receipt) { return null;}
  const { id, processed_by, employee_name, employee_avatar, employee_role, final_amount, updated_at, original_amount, currency, discount_percent, savings, organization} = receipt;

  return (
    <div className={classnames("receipt-detail", className)}>
      {showOrganization && (
        <Link to={`/organizations/${organization.id}`} className="receipt-detail__organization">
          <OrgAvatar
            src={organization.image.medium}
            alt={organization.title}
            className="receipt-detail__organization-avatar"
          />
          <div className="receipt-detail__organization-content">
            <p className="receipt-detail__organization-role f-12 tl">{organization.types[0] && organization.types[0].title}</p>
            <p className="receipt-detail__organization-title f-16 tl">{organization.title}</p>
            <p className="receipt-detail__organization-address f-12 tl">{organization.address}</p>
          </div>
        </Link>
      )}
      {processed_by && (
        <React.Fragment>
          <div className="receipt-detail__initiator">
            <Avatar
              src={employee_avatar && employee_avatar.medium}
              alt={employee_name}
              size={48}
              className="receipt-detail__initiator-avatar"
            />

            <div className="receipt-detail__initiator-right">
              <h2 className="f-15 f-500">{employee_name}</h2>
              <p className="f-14 f-600">{employee_role}</p>
            </div>
          </div>

          {viewProceederReceipts && (
            <Link
              to={`/organizations/${organizationID}/receipts-by/${processed_by}`}
              className="receipt-detail__initiator-view f-14"
            >
              Посмотреть все чеки
            </Link>
          )}
        </React.Fragment>
      )}

      {children}

      <div className="receipt-detail__info">
        <div className="receipt-detail__row row">
          <p className="f-15">Номер заказа</p>
          <p className="f-14">{id}</p>
        </div>

        <div className="receipt-detail__row row">
          <p className="f-15">Дата / время</p>
          <p className="f-14">{moment(updated_at).format(DATE_FORMAT_DD_MM_YYYY_HH_MM)}</p>
        </div>

        <div className="receipt-detail__row row">
          <p className="f-15">Сумма</p>
          <p className="f-14">{original_amount} {currency}</p>
        </div>

        <div className="receipt-detail__row row">
          <p className="f-15">Скидка</p>
          <p className="f-14">{discount_percent}%</p>
        </div>

        <div className="receipt-detail__row row">
          <p className="f-15">Экономия</p>
          <p className="f-14">{savings} {currency}</p>
        </div>

        <div className="receipt-detail__row row">
          <p className="f-15"><b>Итого</b></p>
          <p className="f-14"><b>{final_amount} {currency}</b></p>
        </div>
      </div>

      {onRemove && (
        <Button
          label="Удалить"
          disabled={isRemoving}
          onClick={onRemove}
          className="receipt-detail__remove-btn"
        />
      )}
    </div>
  );
};

export default ReceiptDetail;