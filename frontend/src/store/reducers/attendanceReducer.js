import {METADATA} from '../../common/metadata';
import {GET_ATTENDANCE_STATUS} from '../actionTypes/attendanceTypes';

const initialState = {
  attendanceStatus: { ...METADATA.default, data: null },
};

const attendanceReducer = (state = initialState, action) => {
  switch (action.type) {
    case GET_ATTENDANCE_STATUS.REQUEST:
      return { ...state, attendanceStatus: { ...state.attendanceStatus, ...METADATA.request }};
    case GET_ATTENDANCE_STATUS.SUCCESS:
      return { ...state, attendanceStatus: { ...METADATA.success, data: action.payload }};
    case GET_ATTENDANCE_STATUS.FAILURE:
      return { ...state, attendanceStatus: { ...state.attendanceStatus, ...METADATA.error, error: action.error }};
    default:
      return state;
  }
};

export default attendanceReducer;