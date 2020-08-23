import axios from '../../axios-api';
import {push} from 'react-router-redux';
import Pathes from '../../common/pathes';
import Notify from '../../components/Notification';
import {getMessage} from '../../common/helpers';
import {createFCMToken} from './notificationActions';
import {deleteFCMToken} from '../../firebase_init';
import {
  AUTHENTICATE_USER,
  LOGIN_USER,
  GET_USER,
  SET_TOKEN,
  SET_USER_LOCATION, LOGOUT_USER
} from './actionTypes';

const authenticateRequest = () => ({ type: AUTHENTICATE_USER.REQUEST });
const authenticateSuccess = payload => ({type: AUTHENTICATE_USER.SUCCESS, payload});
const authenticateFailure = error => ({type: AUTHENTICATE_USER.FAILURE, error});

const loginUserRequest = () => ({ type: LOGIN_USER.REQUEST });
const loginUserSuccess = payload => ({ type: LOGIN_USER.SUCCESS, payload });
const loginUserFailure = error => ({ type: LOGIN_USER.FAILURE, error });

const setToken = token => ({ type: SET_TOKEN, token })

const getUserRequest = () => ({ type: GET_USER.REQUEST });
const getUserSuccess = user => ({ type: GET_USER.SUCCESS, user });
const getUserFailure = error => ({ type: GET_USER.FAILURE, error });

export const authenticate = (phone_number) => {
  return dispatch => {
    dispatch(authenticateRequest());
    return axios.post(Pathes.Auth.authenticate, {phone_number}).then(
      response => {
        const {status, data} = response;
        const message = getMessage(data);
        if (status === 200) {
          dispatch(authenticateSuccess(response.data));
          return response.data;
        }

        throw new Error(message)
      }).catch(e =>  dispatch(authenticateFailure(e.message)));
  };
};

export const loginUser = userData => {
  return dispatch => {
    dispatch(loginUserRequest());
    return axios.post(Pathes.Auth.login, userData).then(
      response => {
        const { status, data } = response;
        const message = getMessage(data);
        if (status === 200) {
          dispatch(loginUserSuccess(response.data));
          dispatch(push('/home'));
          const message = `Добро пожаловать, ${response.data.user.full_name}`;
          Notify.success({text: message});
          createFCMToken();
          return { ...data, success: true }
        }

        throw new Error(message)
      }).catch(e => {
        dispatch(loginUserFailure(e.message))
        return { error: e.message, is_wrong_psw: e.message === 'Wrong credentials', success: false }
    });
  };
};

export const logoutUser = () => {
  return (dispatch, getState) => {
    const token = getState().userStore.token;
    token && axios.post(Pathes.Auth.logout, null, { headers: {
      'Authorization': `Token ${token}`
      }}).catch(() => {});
    dispatch({ type: LOGOUT_USER });
    dispatch(push('/auth'));
    deleteFCMToken();
  };
};

export const verifyCode = (phone_number, code) => {
  return dispatch => {
    return axios.post(Pathes.Auth.verifyCode, {phone_number, code}).then(
      response => {
        const {status, data} = response;
        const message = getMessage(data);
        if (status === 200) {
          dispatch(setToken(data && data.token));
          return response.data;
        }

        throw new Error(message)
      }).catch(e => ({error: e.message}));
  }
}

export const resendCode = (phone_number, type) => {
  return () => {
    return axios.post(Pathes.Auth.resendCode, {phone_number, type}).then(
      response => {
        const {status, data} = response;
        const message = getMessage(data);

        if (status === 200) {
          response.data && response.data.message && Notify.success({text: response.data.message})
          return response.data;
        }

        throw new Error(message)
      }).catch(e => ({error: e.message}));
  }
}

export const getUserLocation = () => {
  return async dispatch => {
    try {
      const response = await fetch('https://extreme-ip-lookup.com/json/');
      if (response && response.status === 200) {
        const location = await response.json();
        dispatch({type: SET_USER_LOCATION, location})
      }
    } catch (e) {}
  }
}

export const setPassword = (password) => {
  return () => {
    return axios.post(Pathes.Auth.setPassword, {password}).then(
      response => {
        const {status, data} = response;
        const message = getMessage(data);
        if (status === 200) {
          return {...data, success: true };
        }

        throw new Error(message)
      }).catch(e => ({error: e.message}));
  }
}

export const forgotPassword = phone_number => {
  return () => {
    return axios.post(Pathes.Auth.forgotPassword, {phone_number}).then(
      res => {
        const {status, data} = res;
        const message = getMessage(data);
        if (status === 200) {
          return data;
        }

        throw new Error(message)
      }
    ).catch(e => ({error: e.message}))
  }
}

export const getUser = () => {
  return dispatch => {
    dispatch(getUserRequest())
    return axios.get(Pathes.Profile.get).then(
      res => {
        const {status, data} = res;
        const message = getMessage(data);
        if (status === 200) {
          dispatch(getUserSuccess(data))
          return data;
        }

        throw new Error(message)
      }).catch(e => dispatch(getUserFailure(e.message)));
  }
}

export const changePassword = payload => {
  return () => {
    return axios.post(Pathes.Auth.changePassword, payload).then(
      response => {
        const {status, data} = response;
        const message = getMessage(data);
        if (status === 200) {
          Notify.success({text: message});
          return {
            ...response.data,
            success: true
          };
        }

        throw new Error(message)
      }).catch(e => ({error: e.message}));
  }
}

export const validateOldNumber = () => {
  return () => {
    return axios.post(Pathes.Auth.validateOldNumber).then(
      response => {
        const {status, data} = response;
        if (status === 200) {
          return {
            ...data,
            success: true
          };
        }

        throw new Error(message)
      }).catch(e => ({error: e.message}));
  }
}

export const sendCodeToNewNumber = phone_number => {
  return () => {
    return axios.post(Pathes.Auth.sendCodeToNewNumber, { phone_number }).then(
      response => {
        const {status, data} = response;
        if (status === 200) {
          return {
            ...data,
            success: true
          };
        }

        throw new Error(message)
      }).catch(e => ({ error: e.message }));
  };
}

export const changeAuthNumber = payload => {
  return () => {
    return axios.post(Pathes.Auth.doChangeAndVerifyNewNumber, payload).then(
      response => {
        const {status, data} = response;
        const message = getMessage(data);
        if (status === 200) {
          Notify.success({text: message})
          return {
            ...data,
            success: true
          };
        }

        throw new Error(message)
      }).catch(e => ({ error: e.message }));
  };
}