import axios from '../../axios-api';
import Pathes from '../../common/pathes';
import {getMessage} from '../../common/helpers';
import {getQuery} from '../../common/utils';
import {GET_ATTENDANCE_STATUS} from '../actionTypes/attendanceTypes';
import Notify from '../../components/Notification';

const getAttendanceStatusRequest = () => ({ type: GET_ATTENDANCE_STATUS.REQUEST });
const getAttendanceStatusSuccess = payload => ({ type: GET_ATTENDANCE_STATUS.SUCCESS, payload });
const getAttendanceStatusFailure = error => ({ type: GET_ATTENDANCE_STATUS.FAILURE, error });

export const getEmployeeInfoATD = params => {
  return () => {
    return axios.get(Pathes.Attendance.info + getQuery(params)).then(
      res => {
        const {status, data} = res;
        const message = getMessage(data);
        if (status === 200) {
          return { data, success: true }
        }

        throw new Error(message)
      }).catch(e => ({ error: e.message }));
  }
}

export const recordAttendance = payload => {
  return () => {
    return axios.post(Pathes.Attendance.attendance, payload).then(
      res => {
        const {status, data} = res;
        const message = getMessage(data);
        if (status === 200) {
          Notify.success({ text: 'Пропуск успешно'})
          return { data, success: true }
        }

        if (status === 406 && message === 'Given user is not a member of this organization') {
          Notify.success({ text: 'Этот пользователь не является сотрудником данной организации'})
        }

        throw new Error(message)
      }).catch(e => ({ error: e.message }));
  }
}

export const getAttendanceStatus = (employeeID, params) => {
  return dispatch => {
    dispatch(getAttendanceStatusRequest())
    return axios.get(Pathes.Attendance.stats(employeeID) + getQuery(params)).then(
      res => {
        const {status, data} = res;
        const message = getMessage(data);
        if (status === 200) {
          dispatch(getAttendanceStatusSuccess(data));
          return { data, success: true }
        }

        throw new Error(message)
      }).catch(e =>  dispatch(getAttendanceStatusFailure(e.message)));
  }
}