import React from 'react';
import * as classnames from 'classnames';
import {DEFAULT_CURRENCY} from '../../../common/constants';

const SavingsBlock = ({ total, savings, currency, className }) => {
  return (
    <div className={classnames("row", className)}>
      <p className="f-14" style={{ marginRight: '10px' }}>Сумма: <span className="f-600">{`${total || 0} ${currency || DEFAULT_CURRENCY}`}</span></p>
      <p className="f-14">Экономия: <span className="f-600">{`${savings || 0} ${currency || DEFAULT_CURRENCY}`}</span></p>
    </div>
  );
};

export default SavingsBlock;