import axios from '../../axios-api';
import Pathes from '../../common/pathes';
import Notify from '../../components/Notification';
import {getMessage} from '../../common/helpers';
import {SET_PRE_ORGANIZATION} from './actionTypes';

export const preprocessDiscount = client => {
  return (dispatch, getStore) => {
    const organization = getStore().discountStore.preOrganization && getStore().discountStore.preOrganization.id;
    if (organization && client) {
      return axios.post(Pathes.Discount.preprocess, { client, organization }).then(
        res => {
          const {status, data} = res;
          const message = getMessage(data);
          if (status === 200) {
            return { data, success: true }
          }

          if (data && data.errors && data.errors.client) {
            Notify.info({ text: 'Пользователь не найден' })
          }
          throw new Error(message)
        }).catch(e => ({ error: e.message }));
    }
  }
}

export const setPreOrganization = organization => {
  return dispatch => dispatch({ type: SET_PRE_ORGANIZATION, organization });
}

export const completeDscTransaction = payload => {
  return () => {
    return axios.post(Pathes.Discount.completeTransaction, payload).then(
        res => {
          const {status, data} = res;
          const message = getMessage(data);
          if (status === 200) {
            Notify.success({ text: `Скидка на ${payload.discount_percent}% успешно проведена` });
            return { data, success: true }
          }

          Notify.info({ text: message })
          throw new Error(message)
        }).catch(e => ({ error: e.message }));
    }
}