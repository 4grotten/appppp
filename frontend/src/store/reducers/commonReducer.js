import {METADATA} from '../../common/metadata';
import {GET_CURRENCY, SET_AUTH_CHANGE_CODE, SET_USER_GEO} from '../actions/actionTypes';

const initialState = {
  currency: { ...METADATA.default, data: null },
  authChangeCode: null,
  userGEO: { lat: 42.877300695188, ltd: 74.60012376308443 },
};

const commonReducer = (state = initialState, action) => {
  switch (action.type) {
    case GET_CURRENCY.REQUEST:
      return { ...state, currency: { ...state.currency, ...METADATA.request }}
    case GET_CURRENCY.SUCCESS:
      return { ...state, currency: { ...state.currency, ...METADATA.success, data: action.currency }}
    case GET_CURRENCY.FAILURE:
      return { ...state, currency: { ...state.currency, ...METADATA.error, error: action.error }}
    case SET_AUTH_CHANGE_CODE:
      return { ...state, authChangeCode: action.code}
    case SET_USER_GEO:
      return { ...state, userGEO: action.geo }
    default:
      return state;
  }
};

export default commonReducer;