import {METADATA} from '../../common/metadata';
import {GET_NOTIFICATION_SETTINGS, GET_NOTIFICATIONS, SET_NOTIFICATION_COUNT} from '../actionTypes/notificationTypes';

const initialState = {
  notifications: { ...METADATA.default, data: null },
  settings: { ...METADATA.default, data: null },
  count: 0,
};

const notificationReducer = (state = initialState, action) => {
  switch (action.type) {
    case GET_NOTIFICATIONS.REQUEST:
      return { ...state, notifications: { ...state.notifications, ...METADATA.request }};
    case GET_NOTIFICATIONS.SUCCESS:
      return { ...state, notifications: { ...METADATA.success, data: action.payload }};
    case GET_NOTIFICATIONS.FAILURE:
      return { ...state, notifications: { ...state.notifications, ...METADATA.error, error: action.error }};
    case GET_NOTIFICATION_SETTINGS.REQUEST:
      return { ...state, settings: { ...state.settings, ...METADATA.request }};
    case GET_NOTIFICATION_SETTINGS.SUCCESS:
      return { ...state, settings: { ...METADATA.success, data: action.payload }};
    case GET_NOTIFICATION_SETTINGS.FAILURE:
      return { ...state, settings: { ...state.settings, ...METADATA.error, error: action.error }};
    case SET_NOTIFICATION_COUNT:
      return { ...state, count: action.count };
    default:
      return state;
  }
};

export default notificationReducer;