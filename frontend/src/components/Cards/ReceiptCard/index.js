import React from 'react';
import * as classnames from 'classnames';
import * as moment from 'moment';
import {Link} from 'react-router-dom';
import {DATE_FORMAT_DD_MM_YYYY_HH_MM} from '../../../common/constants';
import './index.scss';

const ReceiptCard = ({ receipt, organization, to, className }) => {
  if (!receipt) { return null }
  const { id, final_amount, discount_percent, savings, updated_at, currency } = receipt;
  return (
   <Link to={to ? to : `/receipts/${id}?org=${organization}`} className={classnames("receipt-card__wrap", className)}>
     <div className="receipt-card row">
       <div className="receipt-card__percent f-14 f-600">{`${discount_percent}%`}</div>
       <div className="receipt-card__check">
         <p className="f-15">Чек: {id}</p>
         <p className="f-14">{moment(updated_at).format(DATE_FORMAT_DD_MM_YYYY_HH_MM)}</p>
       </div>
       <div className="receipt-card__amount">
         <p className="f-15 f-500">{`-${savings} ${currency}`}</p>
         <p className="f-14 f-600">{`${final_amount} ${currency}`}</p>
       </div>
     </div>
   </Link>
  );
};

export default ReceiptCard;