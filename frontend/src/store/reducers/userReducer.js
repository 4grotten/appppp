import {GET_USER, LOGIN_USER, LOGOUT_USER, PROFILE_UPDATE, SET_TOKEN, SET_USER_LOCATION} from '../actions/actionTypes';

const initialState = {
  user: null,
  token: null,
  userLocation: null,
  loading: false,
  error: null,
  loginError: null,
  registerError: null,
};

const userReducer = (state = initialState, action) => {
  switch (action.type) {
    case LOGIN_USER.REQUEST:
      return { ...state, loading: true };
    case LOGIN_USER.SUCCESS:
      return { ...state, token: action.payload.token, user: action.payload.user, loginError: null, loading: false };
    case LOGIN_USER.FAILURE:
      return { ...state, loginError: action.error, loading: false };
    case SET_USER_LOCATION:
      return {...state, userLocation: action.location}
    case SET_TOKEN:
      return {...state, token: action.token}
    case GET_USER.REQUEST:
      return { ...state, loading: true, error: null }
    case GET_USER.SUCCESS:
      return { ...state, user: action.user, loading: false, error: null }
    case GET_USER.FAILURE:
      return { ...state, loading: false, error: action.error }
    case LOGOUT_USER:
      return { ...state, user: null, token: null }
    case PROFILE_UPDATE.REQUEST:
      return { ...state, user: { ...state.user } };
    case PROFILE_UPDATE.SUCCESS:
      return { ...state, user: action.user };
    case PROFILE_UPDATE.FAILURE:
      return { ...state, user: { ...state.user } };
    default:
      return state;
  }
};

export default userReducer;