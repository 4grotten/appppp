import axios from '../../axios-api';
import Pathes from '../../common/pathes';
import {getMessage} from '../../common/helpers';
import {getQuery} from '../../common/utils';
import Notify from '../../components/Notification';
import {
  CREATE_ORG_MESSAGE,
  GET_ORG_MESSAGES, GET_ORG_RECIPIENTS_COUNT,
  GET_SUBSCRIPTION_MESSAGES
} from '../actionTypes/messageTypes';

const getOrgMessagesRequest = () => ({ type: GET_ORG_MESSAGES.REQUEST });
const getOrgMessagesSuccess = payload => ({ type: GET_ORG_MESSAGES.SUCCESS, payload });
const getOrgMessagesFailure = error => ({ type: GET_ORG_MESSAGES.FAILURE, error });

const createOrgMessageRequest = () => ({ type: CREATE_ORG_MESSAGE.REQUEST });
const createOrgMessageSuccess = message => ({ type: CREATE_ORG_MESSAGE.SUCCESS, message });
const createOrgMessageFailure = error => ({ type: CREATE_ORG_MESSAGE.FAILURE, error });

const getOrgRecipientsCountRequest = () => ({ type: GET_ORG_RECIPIENTS_COUNT.REQUEST });
const getOrgRecipientsCountSuccess = payload => ({ type: GET_ORG_RECIPIENTS_COUNT.SUCCESS, payload });
const getOrgRecipientsCountFailure = error => ({ type: GET_ORG_RECIPIENTS_COUNT.FAILURE, error });

const getSubscriptionMessagesRequest = () => ({ type: GET_SUBSCRIPTION_MESSAGES.REQUEST });
const getSubscriptionMessagesSuccess = payload => ({ type: GET_SUBSCRIPTION_MESSAGES.SUCCESS, payload });
const getSubscriptionMessagesFailure = error => ({ type: GET_SUBSCRIPTION_MESSAGES.FAILURE, error });

export const getOrgMessages = (orgID, params, isNext) => {
  return (dispatch, getState) => {
    dispatch(getOrgMessagesRequest());
    return axios.get(Pathes.Messages.organization(orgID) + getQuery(params)).then(
      res => {
        const {status, data} = res;
        const message = getMessage(data);
        if (status === 200) {
          const prevData = getState().messageStore.orgMessages.data;
          if (!isNext || !prevData) {
            dispatch(getOrgMessagesSuccess(data));
            return { ...data, success: true }
          }

          const updatedData = {
            total_count: data.total_count,
            total_pages: data.total_pages,
            list: [ ...prevData.list, ...data.list]
          }
          dispatch(getOrgMessagesSuccess(updatedData));
          return { ...updatedData, success: true }
        }

        throw new Error(message)
      }).catch(e => dispatch(getOrgMessagesFailure(e.message)));
  }
}

export const createOrgMessage = (orgID, payload) => {
  return dispatch => {
    dispatch(createOrgMessageRequest());
    return axios.post(Pathes.Messages.organization(orgID), payload).then(
      res => {
        const {status, data} = res;
        const message = getMessage(data);
        if (status === 201) {
          Notify.success({ text: 'Вы успешно создали сообщение' });
          dispatch(createOrgMessageSuccess(data));
          return { ...data, success: true };
        }
        throw new Error(message)
      }).catch(e => dispatch(createOrgMessageFailure(e.message)));
  }
}

export const getOrgRecipientsCount = orgID => {
  return dispatch => {
    dispatch(getOrgRecipientsCountRequest());
    return axios.get(Pathes.Messages.orgRecipientsCount(orgID)).then(
      res => {
        const {status, data} = res;
        const message = getMessage(data);
        if (status === 200) {
          dispatch(getOrgRecipientsCountSuccess(data));
          return { ...data, success: true };
        }
        throw new Error(message)
      }).catch(e => dispatch(getOrgRecipientsCountFailure(e.message)));
  }
}

export const getSubscriptionMessages = (params, isNext) => {
  return (dispatch, getState) => {
    dispatch(getSubscriptionMessagesRequest());
    return axios.get(Pathes.Messages.subscriptionMSG + getQuery(params)).then(
      res => {
        const {status, data} = res;
        const message = getMessage(data);
        if (status === 200) {
          const prevData = getState().messageStore.subscriptionMessages.data;
          if (!isNext || !prevData) {
            dispatch(getSubscriptionMessagesSuccess(data));
            return { ...data, success: true }
          }

          const updatedData = {
            total_count: data.total_count,
            total_pages: data.total_pages,
            list: [ ...prevData.list, ...data.list]
          }
          dispatch(getSubscriptionMessagesSuccess(updatedData));
          return { ...updatedData, success: true }
        }

        throw new Error(message)
      }).catch(e => dispatch(getSubscriptionMessagesFailure(e.message)));
  }
}
