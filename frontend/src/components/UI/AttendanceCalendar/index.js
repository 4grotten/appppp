import React from 'react';
import moment from 'moment';
import * as classnames from 'classnames';
import Calendar from 'react-calendar';
import { useSwipeable } from 'react-swipeable'
import {DATE_FORMAT_MMMM_YYYY, DATE_FORMAT_YYYY_MM_DD} from '../../../common/constants';
import './index.scss';

const DIRECTIONS = {
  next: 'next',
  prev: 'prev',
}

const AttendanceCalendar = ({ value, onChange, onViewChange, calendar, disableHeader }) => {
  const slide = dir => {
    if (dir === DIRECTIONS.next) {
      const buttonNext = document.querySelector('.react-calendar__navigation__next-button');
      if (buttonNext) {
        buttonNext.click();
      }
    }

    if (dir === DIRECTIONS.prev) {
      const buttonPrev = document.querySelector('.react-calendar__navigation__prev-button');
      if (buttonPrev) {
        buttonPrev.click();
      }
    }
  };

  const handlers = useSwipeable({
    onSwipedLeft: () => slide(DIRECTIONS.next),
    onSwipedRight: () => slide(DIRECTIONS.prev),
    preventDefaultTouchmoveEvent: true,
    trackMouse: true
  });

  const activeDates = (calendar && calendar.map(item => item.date)) || [];

  return (
    <div
      className="attendance-calendar__wrap"
      {...handlers}
    >
      <Calendar
        value={value}
        onChange={onChange}
        onActiveStartDateChange={({ activeStartDate}) => onViewChange(activeStartDate)}
        tileClassName={({ date}) => activeDates.includes(moment(date).format(DATE_FORMAT_YYYY_MM_DD)) ? "attendance-calendar__worked" : moment().isAfter(moment(date), 'day') && "attendance-calendar__not-worked"}
        tileDisabled={({ date }) => moment().isBefore(moment(date), 'month') || moment().isAfter(moment(date), 'month')}
        navigationLabel={({ date }) => moment(date).locale('ru-RU').format(DATE_FORMAT_MMMM_YYYY)}
        className={classnames("attendance-calendar", disableHeader && "attendance-calendar__disable")}
      />
    </div>
  );
};

export default AttendanceCalendar;