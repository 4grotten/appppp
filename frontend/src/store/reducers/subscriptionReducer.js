import {METADATA} from '../../common/metadata';
import {GET_ORG_SUBSCRIPTIONS} from '../actionTypes/subscriptionTypes';

const initialState = {
  subscriptions: { ...METADATA.default, data: null },
};

const SubscriptionReducer = (state = initialState, action) => {
  switch (action.type) {
    case GET_ORG_SUBSCRIPTIONS.REQUEST:
      return { ...state, subscriptions: { ...state.subscriptions, ...METADATA.request }};
    case GET_ORG_SUBSCRIPTIONS.SUCCESS:
      return { ...state, subscriptions: { ...METADATA.success, data: action.payload }};
    case GET_ORG_SUBSCRIPTIONS.FAILURE:
      return { ...state, subscriptions: { ...state.subscriptions, ...METADATA.error, error: action.error }};
    default:
      return state;
  }
};

export default SubscriptionReducer;