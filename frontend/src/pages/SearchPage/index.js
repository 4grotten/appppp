import React from 'react';
import MobileSearchHeader from '../../components/MobileSearchHeader';
import {connect} from 'react-redux';
import OrganizationDscCard from '../../components/Cards/OrganizationDscCard';
import {getSearchResult} from '../../store/actions/homeActions';
import Preloader from '../../components/Preloader';
import EmptyBox from '../../components/EmptyBox';
import InfiniteScroll from 'react-infinite-scroll-component';
import './index.scss';

const DEFAULT_LIMIT = 10;

class SearchPage extends React.Component {
  state = {
    search: '',
    page: 1,
    limit: DEFAULT_LIMIT,
    hasMore: true,
  }

  onSearchChange = e => {
    const { value } = e.target;
    if (value !== this.state.search) {
      this.setState({ ...this.state, search: value, page: 1, hasMore: true });
      this.props.getSearchResult({ ...this.state, search: value, page: 1 });
    }
  }

  getNext = totalPages => {
    if (this.state.page < totalPages) {
      const nextPage = this.state.page + 1
      this.props.getSearchResult({
        ...this.state,
        page: nextPage,
      }, true);

      return this.setState({ ...this.state, hasMore: true, page: nextPage })
    }
    this.setState({ ...this.state, hasMore: false });
  }

  render() {
    const { page } = this.state;
    const { searchResult, homeOrganizations } = this.props;
    const { data, loading } = searchResult;

    let currentList = [];

    if (!data) {
      currentList = homeOrganizations.data ? homeOrganizations.data.list.reduce((acc, category) => {
        acc = [...acc, ...category.organizations]
        return acc;
      }, []) : []
    }

    return (
      <div className="search-page">
        <MobileSearchHeader
          onBack={() => history.push('/home')}
          defaultState={true}
          searchValue={this.state.search}
          onSearchChange={this.onSearchChange}
          onSearchCancel={() => this.props.history.push('/home')}
          title='Поиск'
        />

        <div className="search-page__content">
          <div className="container">
            {(page === 1 && loading)
              ? <Preloader />
              : !data
                ? !currentList.length
                  ? <EmptyBox title="Введите поиск" />
                  : (
                    <React.Fragment>
                      {currentList.map(organization => (
                        <OrganizationDscCard
                          key={organization.id}
                          organization={organization}
                        />
                      ))}
                    </React.Fragment>
                  )
                : (data && !data.total_count)
                  ? <EmptyBox title="Нет совпадений" description={!!this.state.search && 'Поиск не дал результатов'} />
                  : (
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
  homeOrganizations: state.homeStore.homeOrganizations,
  searchResult: state.homeStore.searchResult,
})

const mapDispatchToProps = dispatch => ({
  getSearchResult: (params, isNext) => dispatch(getSearchResult(params, isNext)),
})

export default connect(mapStateToProps, mapDispatchToProps)(SearchPage);