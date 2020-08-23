import {GET_PHONE_NUMBERS, GET_SOCIALS, PROFILE_UPDATE, SET_PHONE_NUMBERS, SET_SOCIALS} from './actionTypes';
import axios from '../../axios-api';
import Pathes from '../../common/pathes';
import Notify from '../../components/Notification';
import {getMessage} from '../../common/helpers';
import {createFCMToken} from './notificationActions';

const updateProfileRequest = () => ({ type: PROFILE_UPDATE.REQUEST });
const updateProfileSuccess = user => ({ type: PROFILE_UPDATE.SUCCESS, user });
const updateProfileFailure = error => ({ type: PROFILE_UPDATE.FAILURE, error });

const getPhoneNumbersRequest = () => ({ type: GET_PHONE_NUMBERS.REQUEST });
const getPhoneNumbersSuccess = phones => ({ type: GET_PHONE_NUMBERS.SUCCESS, phones });
const getPhoneNumbersFailure = error => ({ type: GET_PHONE_NUMBERS.FAILURE, error });

const getSocialsRequest = () => ({ type: GET_SOCIALS.REQUEST });
const getSocialsSuccess = socials => ({ type: GET_SOCIALS.SUCCESS, socials });
const getSocialsFailure = error => ({ type: GET_SOCIALS.FAILURE, error });

const setPhoneNumbersRequest = () => ({ type: SET_PHONE_NUMBERS.REQUEST });
const setPhoneNumbersSuccess = phones => ({ type: SET_PHONE_NUMBERS.SUCCESS, phones });
const setPhoneNumbersFailure = error => ({ type: SET_PHONE_NUMBERS.FAILURE, error });

const setSocialsRequest = () => ({ type: SET_SOCIALS.REQUEST });
const setSocialsSuccess = socials => ({ type: SET_SOCIALS.SUCCESS, socials });
const setSocialsFailure = error => ({ type: SET_SOCIALS.FAILURE, error });

export const updateProfile = data => {
  return dispatch => {
    dispatch(updateProfileRequest())
    return axios.post(Pathes.Profile.update, data).then(
      res => {
        const {status, data} = res;
        const message = getMessage(data);
        if (status === 200) {
          createFCMToken();
          dispatch(updateProfileSuccess(data));
          Notify.success({ text: 'Вы успешно обновили профиль'});
          return {...data, success: true, message};
        }

        throw new Error(message)
      }).catch(e => dispatch(updateProfileFailure(e.message)));
  }
};

export const getPhoneNumbers = () => {
  return (dispatch, getState) => {
    const userID = getState().userStore.user && getState().userStore.user.id;
    dispatch(getPhoneNumbersRequest())
    return axios.get(Pathes.Profile.phones(userID)).then(
      res => {
        const {status, data} = res;
        const message = getMessage(data);
        if (status === 200) {
          dispatch(getPhoneNumbersSuccess(data))
          return data;
        }

        throw new Error(message)
      }).catch(e => dispatch(getPhoneNumbersFailure(e.message)));
  }
}

export const getSocials = () => {
  return (dispatch, getState) => {
    const userID = getState().userStore.user && getState().userStore.user.id;
    dispatch(getSocialsRequest())
    return axios.get(Pathes.Profile.socials(userID)).then(
      res => {
        const {status, data} = res;
        const message = getMessage(data);
        if (status === 200) {
          dispatch(getSocialsSuccess(data))
          return data;
        }

        throw new Error(message)
      }).catch(e => dispatch(getSocialsFailure(e.message)));
  }
}

export const setPhoneNumbers = phonesList => {
  return dispatch => {
    dispatch(setPhoneNumbersRequest())
    return axios.post(Pathes.Profile.setPhones, {phone_numbers: phonesList}).then(
      res => {
        const {status, data} = res;
        const message = getMessage(data);
        if (status === 200) {
          dispatch(setPhoneNumbersSuccess(data));
          Notify.success({text: "Контакты успешно обновлены"})
          return {...data, success: true};
        }

        throw new Error(message)
      }).catch(e => dispatch(setPhoneNumbersFailure(e.message)));
  }
}

export const setSocials = socialList => {
  return dispatch => {
    dispatch(setSocialsRequest())
    return axios.post(Pathes.Profile.setSocials, {networks: socialList}).then(
      res => {
        const {status, data} = res;
        const message = getMessage(data);
        if (status === 200) {
          dispatch(setSocialsSuccess(data));
          Notify.success({text: "Социальные сети успешно обновлены"})
          return {...data, success: true};
        }

        throw new Error(message)
      }).catch(e => dispatch(setSocialsFailure(e.message)));
  }
}

