import React, {useEffect} from 'react';
import { renderRoutes } from 'react-router-config';
import {ROUTES} from './routes';
import { connect } from 'react-redux';
import Navbar from './containers/Navbar';
import {initializeFirebasePush} from './firebase_init';
import Notify from './components/Notification';
import {getNotificationsCount} from './store/actions/notificationActions';
import {NOTIFICATION_TYPES} from './components/Cards/NotificationCard/types';

const allowedRoutes = (token, user) => {
  return ROUTES.filter(route => (route.auth ? route.auth(token, user) : true)) || [];
};

const App = ({ user, token, getNotificationsCount }) => {
  useEffect(() => {
    initializeFirebasePush(onPushMessage);
    !token && Notify.success({ text: 'Скачайте приложение и Вам станут доступны горячие уведомления о новых скидках и возможностях'});
  }, [])

  useEffect(() => {
    getNotificationsCount();
  }, [])

  useEffect(() => {
    window.addEventListener('resize', handleResize);
    handleResize();
    return () => {
      window.removeEventListener('resize', handleResize);
    }
  }, [])

  const handleResize = () => {
    let vh = window.innerHeight * 0.01;
    document.querySelector(':root').style
      .setProperty('--vh', `${vh}px`);
  }

  const onPushMessage = (payload) => {
    payload &&
    payload.data &&
    payload.data.type === NOTIFICATION_TYPES.requested_partnership_recipient &&
    Notify.partnershipRequest(payload)
  }

  return (
    <React.Fragment>
      {renderRoutes(allowedRoutes(token, user), { user } )}
      <Navbar user={user} />
    </React.Fragment>
  )
};

const mapStateToProps = state => ({
    user: state.userStore.user,
    token: state.userStore.token,
})

const mapDispatchToProps = dispatch => ({
  getNotificationsCount: () => dispatch(getNotificationsCount()),
})

export default connect(mapStateToProps, mapDispatchToProps)(App);