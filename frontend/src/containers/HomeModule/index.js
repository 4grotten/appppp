import React from 'react';
import {connect} from 'react-redux';
import {SearchIcon} from '../../components/UI/Icons';
import OrganizationSlider from '../../components/OrganizationSlider';
import {Link} from 'react-router-dom';
import Preloader from '../../components/Preloader';
import BannerSlider from '../../components/BannerSlider';
import InfiniteScroll from 'react-infinite-scroll-component';
import logo from '../../assets/images/logo.png';
import {
  getCategoryDetail,
  getHomeOrganizations,
  getLocalBanners, selectCategory,
} from '../../store/actions/homeActions';
import './index.scss';

const DEFAULT_LIMIT = 5;

class HomeModule extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      page: 1,
      limit: DEFAULT_LIMIT,
      hasMore: true,
    }
  }
  componentDidMount() {
    this.props.getLocalBanners();
    this.props.getHomeOrganizations(this.state);
  }

  getNext = totalPages => {
    if (this.state.page < totalPages) {
      const nextPage = this.state.page + 1
      this.props.getHomeOrganizations({
        ...this.state,
        page: nextPage,
      }, true);

      return this.setState({ ...this.state, hasMore: true, page: nextPage })
    }
    this.setState({ ...this.state, hasMore: false });
  }

  render() {
    const { homeOrganizations, localBanners, selectCategory } = this.props;
    const { data, loading } = homeOrganizations;

    return (
      <div className="home-module">
       <div className="home-module-header__wrap">
         <div className="container">
           <div className="home-module-header row">
             <h1 className="home-module-header__main">
               <div className="home-module-header__logo"><img src={logo} alt="Apofiz Logo"/></div>
               <span className="f-20 f-800">Apofiz</span>
             </h1>
             <Link to="/home/search" className="home-module-header__search" ><SearchIcon /></Link>
           </div>
         </div>
       </div>

        <div className="home-module__content">
          <div className="container">
            <div className="home-module__banners">
              {localBanners.data &&  <BannerSlider banners={localBanners.data} /> }
            </div>
          </div>

          <div className="home-module__categories">
            <div className="container">
              {!data && loading && <Preloader />}
              {data && (
                <InfiniteScroll
                  dataLength={Number(data.list.length) || 0}
                  next={() => this.getNext(data.total_pages)}
                  hasMore={this.state.hasMore}
                  loader={<Preloader />}
                  className="home-module__scroller"
                >
                  {data.list.map(category => (
                    <div key={category.id} className="home-module__category">
                      <div className="home-module__category-top row">
                        <h2 className="f-20 f-400 tl">{category.name}</h2>
                        <Link to={`home/organizations?cat=${category.id}`} className="f-14" onClick={() => selectCategory(category)}>Показать все</Link>
                      </div>
                      <OrganizationSlider
                        organizations={category.organizations}
                        category={category}
                        totalCount={category.organizations_count}
                        className="home-module__category-slider"
                      />
                    </div>
                  ))}
                </InfiniteScroll>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  }
}

const mapStateToProps = state => ({
  homeOrganizations: state.homeStore.homeOrganizations,
  localBanners: state.homeStore.localBanners,
})

const mapDispatchToProps = dispatch => ({
  getHomeOrganizations: (params, isNext) => dispatch(getHomeOrganizations(params, isNext)),
  getLocalBanners: () => dispatch(getLocalBanners()),
  getCategoryDetail: catID => dispatch(getCategoryDetail(catID)),
  selectCategory: category => dispatch(selectCategory(category)),
})

export default connect(mapStateToProps, mapDispatchToProps)(HomeModule);