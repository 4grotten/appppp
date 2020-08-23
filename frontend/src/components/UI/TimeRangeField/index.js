import React from 'react';
import {HOURS24, MINUTES} from './constants';
import './index.scss';

export const DEFAULT_START_H = '09';
export const DEFAULT_START_M = '00';
export const DEFAULT_END_H = '18';
export const DEFAULT_END_M = '00';

const TimeRangeField = (props) => {
  const start = props.start.split(':');
  const end = props.end.split(':');
  const [range, setRange] = React.useState({
    startHour: start[0] || DEFAULT_START_H,
    startMinute: start[1] || DEFAULT_START_M,
    endHour: end[0] || DEFAULT_END_H,
    endMinute: end[1] || DEFAULT_END_M
  });

  const onStartHourChange = async (e) => {
    const current = [e.target.value, range.startMinute].join(':');
    await setRange({...range, startHour: e.target.value});
    props.onStartChange(current);
  };

  const onStartMinuteChange = async (e) => {
    const current = [range.startHour, e.target.value].join(':');
    await setRange({...range, startMinute: e.target.value});
    props.onStartChange(current);
  };

  const onEndHourChange = async (e) => {
    const current = [e.target.value, range.endMinute].join(':');
    await setRange({...range, endHour: e.target.value});
    props.onEndChange(current);
  };

  const onEndMinuteChange = async (e) => {
    const current = [range.endHour, e.target.value].join(':');
    await setRange({...range, endMinute: e.target.value});
    props.onEndChange(current);
  };

  return (
    <div className="time-range-field">
      <label htmlFor="time-range" className="time-range-field__label f-14">Время работы</label>
      <div className="time-range-field__grid">
        <div className="time-range-field__block">
          <span>c</span>
          <select name="select-start-hour" id="select-start-hour" value={range.startHour} onChange={onStartHourChange}>
            {HOURS24.map(hour => <option key={hour} value={hour}>{hour}</option>)}
          </select>
          :
          <select name="select-start-minute" id="select-start-minute" value={range.startMinute} onChange={onStartMinuteChange}>
            {MINUTES.map(hour => <option key={hour} value={hour}>{hour}</option>)}
          </select>
        </div>

        <div className="time-range-field__block">
          <span>до</span>
          <select name="select-end-hour" id="select-end-hour" value={range.endHour} onChange={onEndHourChange}>
            {HOURS24.map(hour => <option key={hour} value={hour}>{hour}</option>)}
          </select>
          :
          <select name="select-end-minute" id="select-end-minute" value={range.endMinute} onChange={onEndMinuteChange}>
            {MINUTES.map(hour => <option key={hour} value={hour}>{hour}</option>)}
          </select>
        </div>
      </div>
    </div>
  );
};

export default TimeRangeField;