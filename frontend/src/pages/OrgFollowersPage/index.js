import React from 'react';
import MobileTopHeader from '../../components/MobileTopHeader';
import UserCard from '../../components/Cards/UserCard';
import {connect} from 'react-redux';
import {getOrgFollowers} from '../../store/actions/organizationActions';
import Preloader from '../../components/Preloader';
import EmptyBox from '../../components/EmptyBox';
import InfiniteScroll from 'react-infinite-scroll-component';
import './index.scss';

const DEFAULT_LIMIT = 10;

class OrgFollowersPage extends React.Component {
  constructor(props) {
    super(props);
    this.organizationID = props.match.params.id;
    this.state = {
      page: 1,
      limit: DEFAULT_LIMIT,
      hasMore: true,
    }
  }

  componentDidMount() {
    this.props.getOrgFollowers(this.organizationID, this.state)
  }

  render() {
    const { orgFollowers, history } = this.props;
    const { page } = this.state;
    const { data, loading } = orgFollowers;

    return (
      <div className="org-followers-page">
        <MobileTopHeader
          onBack={() => history.push(`/organizations/${this.organizationID}`)}
          title="Подписчики"
        />
        <div className="container">
          <div className="org-followers-page__content">
            {(page === 1 && loading)
              ?  <Preloader />
              : (!data || (data && !data.total_count))
                ? <EmptyBox title="Нет подписчиков" description={'Они обязательно будут'} />
                : (
                  <InfiniteScroll
                    dataLength={Number(data.list.length) || 0}
                    next={() => this.getNext(data.total_pages)}
                    hasMore={this.state.hasMore}
                    loader={null}
                  >
                    {data.list.map(user => (
                      <UserCard
                        avatar={user && user.avatar}
                        fullname={user.full_name}
                        description={user.username}
                        withBorder
                        className="org-followers-page__card"
                      />
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
  orgFollowers: state.organizationStore.orgFollowers,
})

const mapDispatchToProps = dispatch => ({
  getOrgFollowers: (orgID, params, isNext) => dispatch(getOrgFollowers(orgID, params, isNext)),
})

export default connect(mapStateToProps, mapDispatchToProps)(OrgFollowersPage);