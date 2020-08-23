import axios from '../../axios-api';
import Pathes from '../../common/pathes';
import Notify from '../../components/Notification';
import {GET_CURRENCY, SET_AUTH_CHANGE_CODE, SET_USER_GEO} from './actionTypes';
import {getMessage} from '../../common/helpers';

const getCurrenciesRequest = () => ({ type: GET_CURRENCY.REQUEST });
const getCurrenciesSuccess = currency => ({ type: GET_CURRENCY.SUCCESS, currency });
const getCurrenciesFailure = error => ({ type: GET_CURRENCY.FAILURE, error });

export const uploadFile = fileObj => {
  return () => {
    let file;
    if (fileObj instanceof FormData) {
      file = fileObj;
    } else {
      file = new FormData();
      file.append('file', fileObj);
    }

    return axios
      .post(Pathes.File.upload, file)
      .then(response => response && response.status === 201 && response.data)
      .catch(() => Notify.info({ text: 'Could not upload image'}));
  };
};

export const getCurrencies = () => {
  return dispatch => {
    dispatch(getCurrenciesRequest());
    return axios.get(Pathes.Common.currency).then(
      res => {
        const {status, data} = res;
        const message = getMessage(data);
        if (status === 200) {
          dispatch(getCurrenciesSuccess(data));
          return { ...data, success: true }
        }

        throw new Error(message)
      }).catch(e => dispatch(getCurrenciesFailure(e.message)));
  }
}

export const setAuthChangeCode = code => {
  return dispatch => {
    dispatch({type: SET_AUTH_CHANGE_CODE, code})
  }
}

export const setUserGEO = geo => {
  return dispatch => dispatch({ type: SET_USER_GEO, geo })
}