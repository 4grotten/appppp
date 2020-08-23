import React from 'react';
import * as classnames from 'classnames';
import Portal from '../../components/Portal';
import {HomeIcon, MainQR, NotificationIcon, RoundCheckIcon} from '../../components/UI/Icons';
import {NavLink} from 'react-router-dom';
import {connect} from 'react-redux';
import {withRouter} from 'react-router';
import MyQR from '../../components/MyQR';
import {setNotificationsAsRead} from '../../store/actions/notificationActions';
import OutsideClickHandler from 'react-outside-click-handler';
import './index.scss';

const EXCLUDED_PATHES = [
  '/auth',
  '/forgot',
  '/proceed-discount',
  '/profile/edit',
  '/profile/edit-contacts',
  '/profile/edit-socials',
  '/profile/edit-auth',
  '/profile/edit-password',
  '/edit-discounts',
  '/edit-main',
  '/create',
  '/scan',
  '/employees',
  '/roles',
  '/attendance-scan',
  '/partners',
];

class Navbar extends React.Component {
  state = {
    showQR: false
  }

  render() {
    const { showQR } = this.state;
    const { user, location, count, setNotificationsAsRead } = this.props;
    if (!user || !!EXCLUDED_PATHES.filter(path => location.pathname.includes(path)).length) {
      return null;
    }

    return (
      <React.Fragment>
        <Portal elementID="menu">
          <div className={classnames("navbar__wrap")}>
            <div className="container">
              <nav className="navbar">
                <NavLink
                  to={'/home'}
                  className="navbar__link"
                  activeClassName={classnames(!showQR && "navbar__link-active")}
                >
                  <HomeIcon />
                  <p className="f-500">Главная</p>
                </NavLink>

                <NavLink
                  to={'/subscriptions'}
                  className="navbar__link"
                  activeClassName={classnames(!showQR && "navbar__link-active")}
                >
                  <RoundCheckIcon />
                  <p className="f-500">Подписки</p>
                </NavLink>

                <OutsideClickHandler
                  onOutsideClick={e => !e.target.classList.contains("my-qr") && this.setState({ showQR: false })}
                  disabled={!showQR}
                >
                  <button
                    type="button"
                    className={classnames("navbar__qr", showQR && "navbar__qr-active")}
                    onClick={() => this.setState({ showQR: !showQR })}
                  >
                    {showQR ? (
                      <svg width="14" height="14" viewBox="0 0 14 14" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M13.3 0.700106C12.9134 0.313506 12.2866 0.313506 11.9 0.700106L6.99998 5.60011L2.09998 0.700106C1.71338 0.313506 1.08658 0.313506 0.699984 0.700106C0.313384 1.08671 0.313384 1.71351 0.699984 2.10011L5.59998 7.00011L0.699984 11.9001C0.313384 12.2867 0.313384 12.9135 0.699984 13.3001C1.08658 13.6867 1.71338 13.6867 2.09998 13.3001L6.99998 8.40011L11.9 13.3001C12.2866 13.6867 12.9134 13.6867 13.3 13.3001C13.6866 12.9135 13.6866 12.2867 13.3 11.9001L8.39998 7.00011L13.3 2.10011C13.6866 1.71351 13.6866 1.08671 13.3 0.700106Z" fill="white"/>
                      </svg>
                    ) : (
                      <MainQR />
                    )}
                  </button>
                </OutsideClickHandler>

                <NavLink
                  to={'/notifications/all'}
                  className="navbar__link"
                  onClick={() => setNotificationsAsRead()}
                  activeClassName={classnames(!showQR && "navbar__link-active")}
                >
                  <div className={classnames("navbar__notification-icon", !!count && "navbar__notification-icon-counter")} data-count={count < 10 ? count : '9+'}>
                    <NotificationIcon />
                  </div>
                  <p className="f-500">Уведомления</p>
                </NavLink>

                <NavLink
                  to={'/profile'}
                  className="navbar__link"
                  activeClassName={classnames(!showQR && "navbar__link-active")}
                >
                  <div className="navbar__avatar">
                    <div className="navbar__avatar-inner">
                      <img src={user.avatar && user.avatar.small} alt={user.full_name} />
                    </div>
                  </div>
                  <p className="f-500">Профиль</p>
                </NavLink>
              </nav>
            </div>
          </div>
        </Portal>

        <Portal elementID="qr">
          <MyQR
            user={user}
            open={showQR}
          />
        </Portal>
      </React.Fragment>
    );
  }
}

const mapStateToProps = state => ({
  user: state.userStore.user,
  count: state.notificationStore.count,
})

const mapDispatchToProps = dispatch => ({
  setNotificationsAsRead: () => dispatch(setNotificationsAsRead()),
})

export default connect(mapStateToProps, mapDispatchToProps)(withRouter(Navbar));