import axios from '../axios-api';
import thunkMiddleware from 'redux-thunk';
import Cookies from 'js-cookie';
import { createBrowserHistory } from 'history';
import { applyMiddleware, combineReducers, compose, createStore } from 'redux';
import { connectRouter, routerMiddleware } from 'connected-react-router';
import {loadFromCookie, saveToCookie} from './cookies';
import {DEFAULT_CURRENCY} from '../common/constants';
import {logoutUser} from './actions/userActions';
import userReducer from './reducers/userReducer';
import profileReducer from './reducers/profileReducer';
import organizationReducer from './reducers/organizationReducer';
import commonReducer from './reducers/commonReducer';
import discountReducer from './reducers/discountReducer';
import homeReducer from './reducers/homeReducer';
import SubscriptionReducer from './reducers/subscriptionReducer';
import statisticReducer from './reducers/statisticReducer';
import {getDataFromLocalStorage} from './localStorage';
import notificationReducer from './reducers/notificationReducer';
import employeeReducer from './reducers/employeeReducer';
import messageReducer from './reducers/messageReducer';
import partnerReducer from './reducers/partnerReducer';
import attendanceReducer from './reducers/attendanceReducer';

export const history = createBrowserHistory();

const rootReducer = combineReducers({
  router: connectRouter(history),
  userStore: userReducer,
  profileStore: profileReducer,
  organizationStore: organizationReducer,
  commonStore: commonReducer,
  discountStore: discountReducer,
  homeStore: homeReducer,
  subscriptionStore: SubscriptionReducer,
  statisticStore: statisticReducer,
  notificationStore: notificationReducer,
  employeeStore: employeeReducer,
  messageStore: messageReducer,
  partnerStore: partnerReducer,
  attendanceStore: attendanceReducer,
});

const composeEnhancers = window.__REDUX_DEVTOOLS_EXTENSION_COMPOSE__ || compose;

const middleware = [thunkMiddleware, routerMiddleware(history)];

const enhancers = composeEnhancers(applyMiddleware(...middleware));

const persistedState = loadFromCookie();

const store = createStore(rootReducer, persistedState, enhancers);

store.subscribe(() => {
  saveToCookie({
    userStore: {
      user: store.getState().userStore.user,
      token: store.getState().userStore.token
    }
  }, { expires: 7 });
});

axios.interceptors.request.use(config => {
  try {
    const token = store.getState().userStore.token;
    const currency = getDataFromLocalStorage('myCurrency') || DEFAULT_CURRENCY;
    if (token) {
      config.headers.Authorization = `Token ${token}`;
      config.headers['Currency'] = currency;
      config.headers['X-CSRFToken'] = Cookies.get('csrftoken');
      config.headers['X-Requested-With'] = 'XMLHttpRequest';
    }
  } catch (e) {
    // do nothing, user is not logged in
  }
  return config;
});

axios.interceptors.response.use(
  response => {
    return response;
  },
  error => {
    if (error && error.response && error.response.status === 401) {
      store.dispatch(logoutUser());
    }
    return error.response;
  }
);

export default store;