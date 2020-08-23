import React from 'react';
import qs from 'qs';
import MobileSearchHeader from '../../components/MobileSearchHeader';
import OrganizationDscCard from '../../components/Cards/OrganizationDscCard';
import {connect} from 'react-redux';
import {getCategoryDetail, getOrgsByCategories} from '../../store/actions/homeActions';
import Preloader from '../../components/Preloader';
import InfiniteScroll from 'react-infinite-scroll-component';
import EmptyBox from '../../components/EmptyBox';
import './index.scss';

const DEFAULT_LIMIT = 10;

class OrganizationsPage extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      partner: null,
      category: null,
      hasMore: true,
      search: '',
      page: 1,
      limit: DEFAULT_LIMIT,
      ...this.parseParams()
    }
  }

  componentDidMount() {
    this.props.getOrgsByCategories(this.state);
    if (this.state.category) {
      this.props.getCategoryDetail(this.state.category);
    }
  }

  onSearchChange = e => {
    const { value } = e.target;
    if (value !== this.state.search) {
      this.setState({ ...this.state, search: value, page: 1, hasMore: true });
      this.props.getOrgsByCategories({ ...this.state, search: value, page: 1 });
    }
  }

  onSearchCancel = () => {
    if (this.state.search !== '') {
      this.setState({ ...this.state, search: '', hasMore: true });
      this.props.getOrgsByCategories({ ...this.state, search: '', page: 1 });
    }
  };

  parseParams = () => {
    const res = qs.parse(this.props.location.search.replace('?', ''));
    const params = {};
    if (res && res.cat) { params.category = res.cat }
    if (res && res.ptr) { params.partner = res.ptr }
    return params;
  }

  getNext = totalPages => {
    if (this.state.page < totalPages) {
      const nextPage = this.state.page + 1
      this.props.getOrgsByCategories({
        ...this.state,
        page: nextPage,
      }, true);

      return this.setState({ ...this.state, hasMore: true, page: nextPage })
    }
    this.setState({ ...this.state, hasMore: false });
  }

  render() {
    const { orgsByCategories, selectedCategory, history } = this.props;
    const { data, loading } = orgsByCategories;

    return (
      <div className="organizations-page">
        <MobileSearchHeader
          onBack={() => history.push('/home')}
          searchValue={this.state.search}
          onSearchChange={this.onSearchChange}
          onSearchCancel={this.onSearchCancel}
          title={selectedCategory && selectedCategory.name}
        />

        <div className="organizations-page__content">
          <div className="container">
            {!data && loading && <Preloader />}
            {data && !data.total_count && (
              <EmptyBox
                title="Организации не найдены"
                description={!!this.state.search && 'Поиск не дал результатов'}
              />
            )}
            {data && (
              <InfiniteScroll
                dataLength={Number(data.list.length) || 0}
                next={() => this.getNext(data.total_pages)}
                hasMore={this.state.hasMore}
                loader={null}
              >
                {data.list.map(organization => (
                  <OrganizationDscCard
                  key={organization.id}
                  organization={organization}
                  className="organizations-page__card"
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
  selectedCategory: state.homeStore.selectedCategory,
  orgsByCategories: state.homeStore.orgsByCategories,
})

const mapDispatchToProps = dispatch => ({
  getOrgsByCategories: (params, isNext) => dispatch(getOrgsByCategories(params, isNext)),
  getCategoryDetail: catID => dispatch(getCategoryDetail(catID)),
})

export default connect(mapStateToProps, mapDispatchToProps)(OrganizationsPage);