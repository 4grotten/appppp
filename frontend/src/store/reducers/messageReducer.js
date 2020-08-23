import {METADATA} from '../../common/metadata';
import {
  GET_ORG_MESSAGES,
  GET_ORG_RECIPIENTS_COUNT,
  GET_SUBSCRIPTION_MESSAGES
} from '../actionTypes/messageTypes';

const initialState = {
  orgMessages: { ...METADATA.default, data: null },
  orgRecipientsCount: { ...METADATA.default, data: null },
  subscriptionMessages: { ...METADATA.default, data: null },
};

const messageReducer = (state = initialState, action) => {
  switch (action.type) {
    case GET_ORG_MESSAGES.REQUEST:
      return { ...state, orgMessages: { ...state.orgMessages, ...METADATA.request }};
    case GET_ORG_MESSAGES.SUCCESS:
      return { ...state, orgMessages: { ...METADATA.success, data: action.payload }};
    case GET_ORG_MESSAGES.FAILURE:
      return { ...state, orgMessages: { ...state.orgMessages, ...METADATA.error, error: action.error }};
    case GET_ORG_RECIPIENTS_COUNT.REQUEST:
      return { ...state, orgRecipientsCount: { ...state.orgRecipientsCount, ...METADATA.request }};
    case GET_ORG_RECIPIENTS_COUNT.SUCCESS:
      return { ...state, orgRecipientsCount: { ...METADATA.success, data: action.payload }};
    case GET_ORG_RECIPIENTS_COUNT.FAILURE:
      return { ...state, orgRecipientsCount: { ...state.orgRecipientsCount, ...METADATA.error, error: action.error }};
    case GET_SUBSCRIPTION_MESSAGES.REQUEST:
      return { ...state, subscriptionMessages: { ...state.subscriptionMessages, ...METADATA.request }};
    case GET_SUBSCRIPTION_MESSAGES.SUCCESS:
      return { ...state, subscriptionMessages: { ...METADATA.success, data: action.payload }};
    case GET_SUBSCRIPTION_MESSAGES.FAILURE:
      return { ...state, subscriptionMessages: { ...state.subscriptionMessages, ...METADATA.error, error: action.error }};
      
    default:
      return state;
  }
};

export default messageReducer;