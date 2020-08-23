import React from 'react';
import OrganizationDscCard from '../../components/Cards/OrganizationDscCard';
import {connect} from 'react-redux';
import {getOrgSubscriptions} from '../../store/actions/subscriptionActions';
import {subscribeOrganization} from '../../store/actions/subscriptionActions';
import Preloader from '../../components/Preloader';
import MobileSearchHeader from '../../components/MobileSearchHeader';
import InfiniteScroll from 'react-infinite-scroll-component';
import './index.scss';

const DEFAULT_LIMIT = 10;

class SubscriptionsPage extends React.Component {
  componentDidMount() {
    this.props.getOrgSubscriptions(this.state);
  }

  state = {
    page: 1,
    limit: DEFAULT_LIMIT,
    search: '',
    hasMore: true,
    unsubscribed: []
  };

  onSearchChange = e => {
    const { value } = e.target;
    if (value !== this.state.search) {
      this.setState({ ...this.state, search: value, page: 1, hasMore: true });
      this.props.getOrgSubscriptions({ ...this.state, search: value, page: 1 });
    }
  }

  onSearchSubmit = e => e.preventDefault();
  onSearchCancel = () => {
    if (this.state.search !== '') {
      this.setState({ ...this.state, search: '', hasMore: true });
      this.props.getOrgSubscriptions({ ...this.state, search: '', page: 1 });
    }
  };

  getNext = totalPages => {
    if (this.state.page < totalPages) {
      const nextPage = this.state.page + 1
      this.props.getOrgSubscriptions({
        ...this.state,
        page: nextPage,
      }, true);

      return this.setState({ ...this.state, hasMore: true, page: nextPage })
    }
    this.setState({ ...this.state, hasMore: false });
  }

  toggleSubscription = orgID => {
    this.props.subscribeOrganization(orgID).then(res => {
      if (res && res.success) {
        if (res.data.is_subscribed === false) {
          return this.setState({ ...this.state, unsubscribed: [...this.state.unsubscribed, orgID] })
        } else if (res.data.is_subscribed === true) {
          return this.setState({ ...this.state, unsubscribed: this.state.unsubscribed.filter(id => id !== orgID) })
        }
      }
    })
  }

  render() {
    const { subscriptions } = this.props
    const { data, loading } = subscriptions;

    return (
      <div className="subscription-page">
        <MobileSearchHeader
          searchValue={this.state.search}
          onSearchChange={this.onSearchChange}
          onSearchSubmit={this.onSearchSubmit}
          onSearchCancel={this.onSearchCancel}
          title="Ваши подписки"
        />

        <div className="subscription-page__content">
          <div className="container">
            {!data && loading && <Preloader />}
            {data && !data.total_count && !this.state.search && (
              <div className="subscription-page__empty">У вас нет подписок</div>
            )}
            {data && !data.total_count && this.state.search && (
              <div className="subscription-page__empty">Поиск не дал результатов</div>
            )}
            {data && (
              <InfiniteScroll
                dataLength={Number(data.list.length) || 0}
                next={() => this.getNext(data.total_pages)}
                hasMore={this.state.hasMore}
                loader={null}
              >
                {data.list.map(organization => (
                  <div key={organization.id} className="subscription-page__item row">
                    <OrganizationDscCard organization={organization} className="subscription-page__item-card" />
                    {this.state.unsubscribed.includes(organization.id) ? (
                      <button type="button" className="subscription-page__subscribe" onClick={() => this.toggleSubscription(organization.id)} >
                        <svg width="22" height="22" viewBox="0 0 22 22" fill="none" xmlns="http://www.w3.org/2000/svg">
                          <path d="M14.924 0C16.8822 0.0206819 17.8787 0.231702 18.912 0.784308C19.9011 1.31328 20.6833 2.09549 21.2123 3.08458C21.7649 4.11786 21.9759 5.11438 21.9966 7.07256V14.924C21.9759 16.8822 21.7649 17.8787 21.2123 18.912C20.6833 19.9011 19.9011 20.6833 18.912 21.2123C17.8787 21.7649 16.8822 21.9759 14.924 21.9966H7.07256C5.11438 21.9759 4.11786 21.7649 3.08458 21.2123C2.09549 20.6833 1.31328 19.9011 0.784308 18.912C0.231702 17.8787 0.0206819 16.8822 0 14.924V7.07256C0.0206819 5.11438 0.231702 4.11786 0.784308 3.08458C1.31328 2.09549 2.09549 1.31328 3.08458 0.784308C4.11786 0.231702 5.11438 0.0206819 7.07256 0H14.924ZM14.5886 1.99829H7.408L6.85062 2.00317C5.37134 2.03122 4.70897 2.18363 4.02777 2.54793C3.38723 2.8905 2.8905 3.38723 2.54793 4.02777C2.18363 4.70897 2.03122 5.37134 2.00317 6.85062L1.99829 7.408V14.5886L2.00317 15.146C2.03122 16.6252 2.18363 17.2876 2.54793 17.9688C2.8905 18.6094 3.38723 19.1061 4.02777 19.4486C4.70897 19.813 5.37134 19.9654 6.85062 19.9934L7.408 19.9983H14.5886L15.146 19.9934C16.6252 19.9654 17.2876 19.813 17.9688 19.4486C18.6094 19.1061 19.1061 18.6094 19.4486 17.9688C19.813 17.2876 19.9654 16.6252 19.9934 15.146L19.9983 14.5886V7.408L19.9934 6.85062C19.9654 5.37134 19.813 4.70897 19.4486 4.02777C19.1061 3.38723 18.6094 2.8905 17.9688 2.54793C17.2876 2.18363 16.6252 2.03122 15.146 2.00317L14.5886 1.99829ZM11 6C11.5523 6 12 6.44772 12 7V10H15C15.5523 10 16 10.4477 16 11C16 11.5523 15.5523 12 15 12H12V15C12 15.5523 11.5523 16 11 16C10.4477 16 10 15.5523 10 15V12H7C6.44772 12 6 11.5523 6 11C6 10.4477 6.44772 10 7 10H10V7C10 6.44772 10.4477 6 11 6Z" fill="#4285F4"/>
                        </svg>
                      </button>
                    ) : (
                      <button type="button" className="subscription-page__unsubscribe" onClick={() => {
                        const allow = window.confirm('Вы уверены, что хотите отписаться от организации?');
                        allow && this.toggleSubscription(organization.id);
                      }}>
                        <svg width="22" height="22" viewBox="0 0 22 22" fill="none" xmlns="http://www.w3.org/2000/svg">
                          <path d="M14.924 0C16.8822 0.0206819 17.8787 0.231702 18.912 0.784308C19.9011 1.31328 20.6833 2.09549 21.2123 3.08458C21.7649 4.11786 21.9759 5.11438 21.9966 7.07256V14.924C21.9759 16.8822 21.7649 17.8787 21.2123 18.912C20.6833 19.9011 19.9011 20.6833 18.912 21.2123C17.8787 21.7649 16.8822 21.9759 14.924 21.9966H7.07256C5.11438 21.9759 4.11786 21.7649 3.08458 21.2123C2.09549 20.6833 1.31328 19.9011 0.784308 18.912C0.231702 17.8787 0.0206819 16.8822 0 14.924V7.07256C0.0206819 5.11438 0.231702 4.11786 0.784308 3.08458C1.31328 2.09549 2.09549 1.31328 3.08458 0.784308C4.11786 0.231702 5.11438 0.0206819 7.07256 0H14.924ZM14.5886 1.99829H7.408L6.85062 2.00317C5.37134 2.03122 4.70897 2.18363 4.02777 2.54793C3.38723 2.8905 2.8905 3.38723 2.54793 4.02777C2.18363 4.70897 2.03122 5.37134 2.00317 6.85062L1.99829 7.408V14.5886L2.00317 15.146C2.03122 16.6252 2.18363 17.2876 2.54793 17.9688C2.8905 18.6094 3.38723 19.1061 4.02777 19.4486C4.70897 19.813 5.37134 19.9654 6.85062 19.9934L7.408 19.9983H14.5886L15.146 19.9934C16.6252 19.9654 17.2876 19.813 17.9688 19.4486C18.6094 19.1061 19.1061 18.6094 19.4486 17.9688C19.813 17.2876 19.9654 16.6252 19.9934 15.146L19.9983 14.5886V7.408L19.9934 6.85062C19.9654 5.37134 19.813 4.70897 19.4486 4.02777C19.1061 3.38723 18.6094 2.8905 17.9688 2.54793C17.2876 2.18363 16.6252 2.03122 15.146 2.00317L14.5886 1.99829ZM14.6429 7.69289C15.0334 7.30236 15.6666 7.30236 16.0571 7.69289C16.4476 8.08341 16.4476 8.71658 16.0571 9.1071L10.4571 14.7071C10.0666 15.0976 9.43342 15.0976 9.04289 14.7071L6.44289 12.1071C6.05237 11.7166 6.05237 11.0834 6.4429 10.6929C6.83342 10.3024 7.46659 10.3024 7.85711 10.6929L9.75 12.5858L14.6429 7.69289Z" fill="#818C99"/>
                        </svg>
                      </button>
                    )}
                  </div>
                ))}
              </InfiniteScroll>
            )}
          </div>
        </div>
      </div>
    );
  }
}

const mapStateToProps = state => ({
 subscriptions: state.subscriptionStore.subscriptions,
})

const mapDispatchToProps = dispatch => ({
  getOrgSubscriptions: (params, isNext) => dispatch(getOrgSubscriptions(params, isNext)),
  subscribeOrganization: orgID => dispatch(subscribeOrganization(orgID)),
})

export default connect(mapStateToProps, mapDispatchToProps)(SubscriptionsPage);