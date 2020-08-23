import React, {Component} from 'react';
import MobileSearchHeader from '../../components/MobileSearchHeader';
import {HeaderNav} from '../../components/HeaderNav';
import {connect} from 'react-redux';
import {Link} from 'react-router-dom';
import {ArrowRight} from '../../components/UI/Icons';
import {getRoles} from '../../store/actions/employeeActions';
import Preloader from '../../components/Preloader';
import EmptyBox from '../../components/EmptyBox';
import InfiniteScroll from 'react-infinite-scroll-component';
import './index.scss'

class RolesPage extends Component {
  constructor(props) {
    super(props);
    const orgID = props.match.params.id;
    this.routes = [
      { label: 'Сотрудники', path: `/organizations/${orgID}/employees`},
      { label: 'Должности', path: `/organizations/${orgID}/roles`},
    ];
    this.state = {
      step: 0,
      organization: orgID,
      page: 1,
      limit: 10,
      search: '',
    }
  }

  componentDidMount() {
    this.props.getRoles(this.state);
  }

  getNext = totalPages => {
    if (this.state.page < totalPages) {
      const nextPage = this.state.page + 1
      this.props.getRoles({
        ...this.state,
        page: nextPage,
      }, true);

      return this.setState({ ...this.state, hasMore: true, page: nextPage })
    }
    this.setState({ ...this.state, hasMore: false });
  }

  onSearchChange = e => {
    const { value } = e.target;
    if (value !== this.state.search) {
      this.setState({ ...this.state, search: value, page: 1, hasMore: true });
      this.props.getRoles({ ...this.state, search: value, page: 1 });
    }
  }

  onSearchCancel = () => {
    if (this.state.search !== '') {
      this.setState({ ...this.state, search: '', hasMore: true });
      this.props.getRoles({ ...this.state, search: '', page: 1 });
    }
  };

  render() {
    const { roles, history } = this.props;
    const { page, search, organization } = this.state;
    const { data, loading } = roles;

    return (
      <div className="roles-page">
        <MobileSearchHeader
          onBack={() => history.push(`/organizations/${organization}`)}
          searchValue={search}
          onSearchChange={this.onSearchChange}
          onSearchCancel={this.onSearchCancel}
          renderHeader={() => <HeaderNav routes={this.routes} />}
        />

        <div className="container">
          <div className="roles-page__content">
            <div className="roles-page__list">
              {(page === 1 && loading)
                ?  <Preloader />
                : (!data || (data && !data.total_count))
                  ? <EmptyBox title="Нет должностей" description={!!search && 'Поиск не дал результатов'} />
                  : (
                    <InfiniteScroll
                      dataLength={Number(data.list.length) || 0}
                      next={() => this.getNext(data.total_pages)}
                      hasMore={this.state.hasMore}
                      loader={null}
                    >
                      {data && data.list.map(role => (
                        <Link
                          className="roles-page__role f-16"
                          key={role.id}
                          to={`roles/${role.id}`}
                        >
                          {role.title}
                          <ArrowRight />
                        </Link>
                      ))}
                    </InfiniteScroll>
                  )}
            </div>
            <Link to='roles/add' className="roles-page__add f-15 f-500" >
              Создать должность
            </Link>
          </div>
        </div>
      </div>
    );
  }
}

const mapStateToProps = state => ({
  roles: state.employeeStore.roles,
})

const mapDispatchToProps = dispatch => ({
  getRoles: (params, isNext) => dispatch(getRoles(params, isNext)),
})

export default connect(mapStateToProps, mapDispatchToProps)(RolesPage);