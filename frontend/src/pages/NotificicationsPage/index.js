import React from 'react';
import qs from 'qs';
import {connect} from 'react-redux';
import MobileTopHeader from '../../components/MobileTopHeader';
import {NavLink} from 'react-router-dom';
import NotificationCard from '../../components/Cards/NotificationCard';
import InfiniteScroll from 'react-infinite-scroll-component';
import {NotificationIcon} from '../../components/UI/Icons';
import EmptyBox from '../../components/EmptyBox';
import MobileMenu from '../../components/MobileMenu';
import RowToggle from '../../components/UI/RowToggle';
import {Formik} from 'formik';
import {
  getNotifications,
  getNotificationSettings, setNotificationsAsRead,
  updateNotificationSettings
} from '../../store/actions/notificationActions';
import {rejectPartnership, setPartnershipPermissions} from '../../store/actions/partnerActions';
import './index.scss';

const NOTIFICATION_MODES = ['discount', 'system', 'partner', 'personal'];

class NotificationsPage extends React.Component {
  constructor(props) {
    let { mode } = qs.parse(props.match.params);
    super(props);
    this.state = {
      mode: this.getMode(mode),
      page: 1,
      limit: 10,
      hasMore: true,
      showMenu: false,
    }
  }

  componentDidMount() {
    this.props.getNotificationSettings();
    this.props.getNotifications(this.state);
  }

  componentDidUpdate(prevProps, prevState, snapshot) {
    if (prevProps.match.params.mode !== this.props.match.params.mode) {
      const updatedState = {
        ...this.state,
        mode: this.getMode(this.props.match.params.mode),
        hasMore: true,
        page: 1
      }

      this.setState(updatedState);
      this.props.getNotifications(updatedState);
    }
  }

  componentWillUnmount() {
    this.props.setNotificationsAsRead();
  }

  getMode = mode => {
    if (!mode) { return null; }
    return NOTIFICATION_MODES.includes(mode.toLowerCase()) ? mode.toLowerCase() : null;
  }

  getNext = totalPages => {
    if (this.state.page < totalPages) {
      const nextPage = this.state.page + 1
      this.props.getNotifications({
        ...this.state,
        page: nextPage,
      }, true);

      return this.setState({ ...this.state, hasMore: true, page: nextPage })
    }
    this.setState({ ...this.state, hasMore: false });
  }

  toggleMenu = menuState => {
    this.setState({ ...this.state, showMenu: menuState })
  }

  render() {
    const { notifications, settings, updateNotificationSettings, setPartnershipPermissions, rejectPartnership, history } = this.props;
    const { data, loading } = notifications;

    return (
      <div className="notifications-page">
        <MobileTopHeader
          title="Уведомления"
          onMenu={() => this.toggleMenu(!this.state.showMenu)}
        />

        <div className="container">
          <nav className="notifications-page__nav">
            <NavLink
              to="/notifications/all"
              className="notifications-page__nav-link"
              activeClassName="notifications-page__nav-link-active"
            >Все</NavLink>

            <NavLink
              to="/notifications/discount"
              className="notifications-page__nav-link"
              activeClassName="notifications-page__nav-link-active"
            >Скидки</NavLink>

            <NavLink
              to="/notifications/personal"
              className="notifications-page__nav-link"
              activeClassName="notifications-page__nav-link-active"
            >Личные</NavLink>

            <NavLink
              to="/notifications/system"
              className="notifications-page__nav-link"
              activeClassName="notifications-page__nav-link-active"
            >Системные</NavLink>
          </nav>

          <div className="notifications-page__content">
            {((data && !data.total_count) || (!data && !loading)) && (
              <EmptyBox
                renderIcon={() => <NotificationIcon />}
                title="У вас пока нет уведомлений"
                description="Вам они обязательно будут приходить, для хорошего настроения"
                className="notifications-page__empty"
              />
            )}

            {data && (
              <InfiniteScroll
                dataLength={Number(data.list.length) || 0}
                next={() => this.getNext(data.total_pages)}
                hasMore={this.state.hasMore}
                loader={null}
              >
                {data.list.map(item => (
                  <NotificationCard
                    key={item.id}
                    card={item}
                    onAcceptPartnership={((id, redirectURL) => setPartnershipPermissions(id, {}).then(res => res && res.success && history.push(redirectURL)))}
                    onRejectPartnership={(id) => rejectPartnership(id)}
                    className="notifications-page__item"
                  />
                ))}
              </InfiniteScroll>
            )}
          </div>
        </div>

        <MobileMenu
          isOpen={this.state.showMenu}
          contentLabel="Настройка уведомлений"
          onRequestClose={() => this.toggleMenu(false)}
        >
          <Formik
            onSubmit={() => null}
            enableReinitialize
            initialValues={{
              discount_notifications: !!settings.data && settings.data.discount_notifications,
              organization_notifications: !!settings.data && settings.data.organization_notifications,
              private_notifications: !!settings.data && settings.data.private_notifications,
            }}
          >
            {({ values, handleSubmit, handleChange }) => (
              <form className="notifications-page__menu-list" onSubmit={handleSubmit}>
                <RowToggle
                  label="Уведомления о скидках"
                  name="discount_notifications"
                  checked={values.discount_notifications}
                  onChange={(e) => {
                    updateNotificationSettings({ ...values, [e.target.name]: !values[e.target.name]});
                    handleChange(e);
                  }}
                />
                <RowToggle
                  label="Уведомления подписки"
                  name="organization_notifications"
                  checked={values.organization_notifications}
                  onChange={(e) => {
                    updateNotificationSettings({ ...values, [e.target.name]: !values[e.target.name]});
                    handleChange(e);
                  }}
                />
                <RowToggle
                  label="Системные уведомления"
                  name="private_notifications"
                  checked={values.private_notifications}
                  onChange={(e) => {
                    updateNotificationSettings({ ...values, [e.target.name]: !values[e.target.name]});
                    handleChange(e);
                  }}
                />
              </form>
            )}
          </Formik>
        </MobileMenu>
      </div>
    );
  }
}

const mapStateToProps = state => ({
  notifications: state.notificationStore.notifications,
  settings: state.notificationStore.settings,
})

const mapDispatchToProps = dispatch => ({
  getNotifications: (params, isNext) => dispatch(getNotifications(params, isNext)),
  getNotificationSettings: () => dispatch(getNotificationSettings()),
  updateNotificationSettings: settings => dispatch(updateNotificationSettings(settings)),
  setNotificationsAsRead: () => dispatch(setNotificationsAsRead()),
  rejectPartnership: id => dispatch(rejectPartnership(id)),
  setPartnershipPermissions: (id, payload) => dispatch(setPartnershipPermissions(id, payload)),
})

export default connect(mapStateToProps, mapDispatchToProps)(NotificationsPage);