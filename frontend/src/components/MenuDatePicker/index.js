import React from 'react';
import * as moment from 'moment';
import * as classnames from 'classnames';
import {Formik} from "formik";
import Button from '../UI/Button';
import DatePicker from '../UI/DatePicker';
import {DATE_FORMAT_DD_MMMM_YYYY} from '../../common/constants';
import {DoneIcon} from '../UI/Icons';
import './index.scss';

export const DEFAULT_DATE_LABEL = 'За все время';
const today = moment().startOf('day');

const DATE_RANGES = [
  {
    label: 'Сегодня',
    range: {
      start: today.clone().startOf('day'),
      end: today.clone().endOf('day'),
    }
  },
  {
    label: 'Эта неделя',
    range: {
      start: today.clone().startOf('isoWeek'),
      end: today.clone().endOf('isoWeek'),
    }
  },
  {
    label: 'Прошлая неделя',
    range: {
      start: today.clone().startOf('isoWeek').subtract(1, 'isoWeek'),
      end: today.clone().endOf('isoWeek').subtract(1, 'isoWeek'),
    }
  },
  {
    label: 'Этот месяц',
    range: {
      start: today.clone().startOf('month'),
      end: today.clone().endOf('month'),
    }
  },
  {
    label: 'Прошлый месяц',
    range: {
      start: today.clone().startOf('month').subtract(1, 'month'),
      end: today.clone().endOf('month').subtract(1, 'month'),
    }
  },
]

const MenuDatePicker = ({ start, end, onChange }) => {
  const isCurrentlySelected = (range) => {
    if (!start && !end) { return false; }
    return moment(start).isSame(range.start);
  };

  return (
    <Formik
      enableReinitialize
      onSubmit={values => onChange(values)}
      initialValues={{
        start,
        end
      }}
    >
      {({ values, setFieldValue, handleSubmit }) => (
        <form onSubmit={handleSubmit}>
          <div
            onClick={() => onChange({ start: null, end: null })}
            className={classnames("menu-date-picker__set", (!start && !end) && "menu-date-picker__set-active")}
          >
            <p className="menu-date-picker__set-title f-15">{DEFAULT_DATE_LABEL}</p>
            {<DoneIcon className={classnames("menu-date-picker__set-done-icon", (!start && !end) && "menu-date-picker__set-done-icon-visible")} />}
          </div>
          {DATE_RANGES.map(option => (
            <div
              key={option.label}
              onClick={() => onChange({
                start: option.range.start.toDate(),
                end: option.range.end.toDate()
              })}
              className={classnames("menu-date-picker__set", isCurrentlySelected(option.range) && "menu-date-picker__set-active")}

            >
              <p className="menu-date-picker__set-title f-15">{option.label}</p>
              <p className="menu-date-picker__set-value f-14">
                {option.range.start.locale('ru').format(DATE_FORMAT_DD_MMMM_YYYY)} - {option.range.end.locale('ru').format(DATE_FORMAT_DD_MMMM_YYYY)}
              </p>
              <DoneIcon className="menu-date-picker__set-done-icon" />
            </div>
          ))}

          <div className="menu-date-picker__title f-16 f-600">Настроить свое время</div>
          <DatePicker
            label="Дата начала"
            value={values.start}
            onChange={date => setFieldValue('start', date)}
            className="menu-date-picker__date"
          />
          <DatePicker
            label="Дата конца"
            value={values.end}
            onChange={date => setFieldValue('end', date)}
            className="menu-date-picker__date"
          />
          <Button type="submit" onSubmit={handleSubmit} label="Применить"  className="menu-date-picker__apply"/>
        </form>
      )}
    </Formik>
  );
};

export default MenuDatePicker;