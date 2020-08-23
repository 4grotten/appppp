import * as React from 'react'
import {Link} from 'react-router-dom';
import OrganizationCard from '../../components/Cards/OrganizationCard';
import EditIcon from '../../components/UI/Icons/EditIcon';
import {connect} from 'react-redux';
import {getUser} from '../../store/actions/userActions';
import {getOrganizationsList} from '../../store/actions/organizationActions';
import YourSavings from '../../components/YourSavings';
import {InsightIcon, ScanIcon} from '../../components/UI/Icons';
import Preloader from '../../components/Preloader';
import {getStatisticSummary} from '../../store/actions/statisticActions';
import {getDataFromLocalStorage} from '../../store/localStorage';
import {DEFAULT_CURRENCY} from '../../common/constants';
import InfiniteScroll from 'react-infinite-scroll-component';
import './index.scss';

const DEFAULT_LIMIT = 10;

class ProfileModule extends React.Component {
  componentDidMount() {
    this.props.getUser();
    this.props.getStatisticSummary();
    this.props.getOrganizationsList(this.state);
  }

  state = {
    page: 1,
    limit: DEFAULT_LIMIT,
    hasMore: true,
  }

  getNext = totalPages => {
    if (this.state.page < totalPages) {
      const nextPage = this.state.page + 1
      this.props.getOrganizationsList({
        ...this.state,
        page: nextPage,
      }, true);

      return this.setState({ ...this.state, hasMore: true, page: nextPage })
    }
    this.setState({ ...this.state, hasMore: false });
  }

  render () {
    const { user, orgList, summary } = this.props;
    const myCurrency = getDataFromLocalStorage('myCurrency') || DEFAULT_CURRENCY;
    const { data, loading } = orgList;

    return (
        <div className="profile-module">
          <div className="profile-module__header-wrap">
            <div className="container">
              <Link to="/profile/edit" className="profile-module__header" >
                <EditIcon />
                <h1 className="profile-module__title f-16 f-600 tl">{`@${user && user.username || 'nickname'}`}</h1>
              </Link>
            </div>
          </div>

          <div className="container">
            <div className="profile-module__content">
              <Link to="/profile/edit">
                <div className="profile-module__user">
                  <div className="profile-module__user-left">
                    <div className="profile-module__user-image">
                      <img src={user && user.avatar && user.avatar.file} alt={user && user.full_name || 'Avatar'}/>
                    </div>
                  </div>
                  <div className="profile-module__user-right">
                    <h4 className="profile-module__user-fullname f-600 f-17">{user && user.full_name}</h4>
                    <p className="profile-module__user-id f-600 f-14">ID {user && user.id}</p>
                  </div>
                </div>
              </Link>

              <YourSavings
                savings={summary && summary.total_savings || 0}
                myCurrency={myCurrency}
              />

              <div className="profile-module__links">
                <Link to="/statistics" className="profile-module__link" >
                  <InsightIcon />
                  <span>Ваша статистика</span>
                </Link>

                <Link to="/scan" className="profile-module__link" >
                  <ScanIcon />
                  <span>QR Scan</span>
                </Link>
              </div>

              <div className="profile-module__organizations">
                <h3>Ваши организации</h3>
                {!data && loading && <Preloader className="profile-module__organizations-preloader" />}

                {data && (
                  <InfiniteScroll
                    dataLength={Number(data.list.length) || 0}
                    next={() => this.getNext(data.total_pages)}
                    hasMore={this.state.hasMore}
                    loader={null}
                  >
                    {data.list.map(org => (
                      <OrganizationCard
                        key={org.id}
                        id={org.id}
                        title={org.title}
                        image={org.image && org.image.medium}
                        description={org.role}
                        className="profile-module__organization"
                      />
                    ))}
                  </InfiniteScroll>
                )}
                {data && !data.list.length && <div>У Вас нет организаций</div> }
                <Link className="profile-module__organizations-add" to="/organizations/create">Открыть организацию</Link>
              </div>
            </div>
          </div>
        </div>
    )
  }
}

const mapStateToProps = state => ({
  summary: state.statisticStore.summary,
  user: state.userStore.user,
  orgList: state.organizationStore.orgList,
});

const mapDispatchToProps = dispatch => ({
  getUser: () => dispatch(getUser()),
  getStatisticSummary: () => dispatch(getStatisticSummary()),
  getOrganizationsList: (params, isNext) => dispatch(getOrganizationsList(params, isNext)),
})

export default connect(mapStateToProps, mapDispatchToProps)(ProfileModule);