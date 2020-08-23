import React from 'react';
import * as classnames from 'classnames';
import * as moment from 'moment';
import Calendar from 'react-calendar';
import {DATE_FORMAT_DD_MMMM_YYYY} from '../../../common/constants';
import {ArrowRight} from '../Icons';
import './index.scss';

const DatePicker = ({ value, onChange, renderContent, label, className }) => {
  const [ show, toggleShow ] = React.useState(false);
  return (
    <div className={classnames("date-picker__container", className)}>
      <div className="date-picker__content" onClick={() => toggleShow(!show)}>
        {renderContent ? renderContent(show, value) : (
          <div className="date-picker__input-container row">
            <div className="date-picker__input">
              <p className="date-picker__input-title f-15">{label || "Дата" }</p>
              <p className="date-picker__input-date f-14">{value ? moment(value).locale('ru').format(DATE_FORMAT_DD_MMMM_YYYY) : ''}</p>
            </div>
            <ArrowRight className={classnames("date-picker__input-icon", show && "date-picker__input-icon-active" )} />
          </div>
        )}
      </div>

      <div className={classnames("date-picker__dropdown", show && "date-picker__dropdown-active")}>
        <Calendar
          onChange={(date) => {
            onChange(date);
            toggleShow(false);
          }}
          value={value}
        />
      </div>
    </div>
  );
};

export default DatePicker;