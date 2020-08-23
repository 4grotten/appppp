import React, {Component} from 'react';
import {connect} from 'react-redux';
import * as moment from 'moment';
import InfiniteScroll from 'react-infinite-scroll-component';
import MobileSearchHeader from '../../components/MobileSearchHeader';
import Preloader from '../../components/Preloader';
import EmptyBox from '../../components/EmptyBox';
import PartnerCard from '../../components/Cards/PartnerCard';
import SavingsBlock from '../../components/UI/SavingsBlock';
import MenuDatePicker from '../../components/MenuDatePicker';
import MobileMenu from '../../components/MobileMenu';
import {DATE_FORMAT_DD_MMMM_YYYY} from '../../common/constants';
import {getOrgPartnerStatisticSummary} from '../../store/actions/statisticActions';
import {getOrgPartners} from '../../store/actions/partnerActions';
import './index.scss';

const DEFAULT_LIMIT = 10;

class OrgPartnerStatisticsPage extends Component {
  constructor(props) {
    super(props);
    this.organization = props.match.params.id;
    this.state = {
      page: 1,
      start: null,
      end: null,
      search: '',
      limit: DEFAULT_LIMIT,
      showMenu: false,
      hasMore: true,
    }
  }

  componentDidMount() {
    this.props.getOrgPartners(this.organization, this.state);
    this.props.getOrgPartnerStatisticSummary(this.organization, {
      start: this.state.start,
      end: this.state.end
    });
  }

  getNext = totalPages => {
    if (this.state.page < totalPages) {
      const nextPage = this.state.page + 1
      this.props.getOrgPartners(this.organization, {
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
      this.props.getOrgPartners(this.organization, { ...this.state, search: value, page: 1 });
    }
  }

  onSearchCancel = () => {
    if (this.state.search !== '') {
      this.setState({ ...this.state, search: '', hasMore: true });
      this.props.getOrgPartners(this.organization, { ...this.state, search: '', page: 1 });
    }
  };

  render() {
    const { orgPartners, orgPartnersSummary, history } = this.props;
    const { data, loading } = orgPartners;
    const { page, search, start, end } = this.state;

    return (
      <div className="org-partner-statistics-page">
        <MobileSearchHeader
          onBack={() => history.push(`/organizations/${this.organization}`)}
          title="Партнеры"
          searchValue={search}
          onSearchChange={this.onSearchChange}
          onSearchCancel={this.onSearchCancel}
        />

        <div className="org-partner-statistics-page__content">
          <div className="org-partner-statistics-page__top" onClick={() => this.setState({ ...this.state, showMenu: true })}>
            <div className="container">
              <SavingsBlock
                total={orgPartnersSummary && orgPartnersSummary.total_spent}
                savings={orgPartnersSummary && orgPartnersSummary.total_savings}
                currency={orgPartnersSummary && orgPartnersSummary.currency}
                className="org-partner-statistics-page__summary"
              />
              <div className="org-partner-statistics-page__calendar f-14 f-500">
                {(start && end)
                  ? `с ${moment(start).locale('ru').format(DATE_FORMAT_DD_MMMM_YYYY)} - по ${moment(end).locale('ru').format(DATE_FORMAT_DD_MMMM_YYYY)}`
                  : 'За все время'
                }
              </div>
            </div>
          </div>

          <div className="org-partner-statistics-page__list">
            <div className="container">
              {(page === 1 && loading)
                ? <Preloader />
                : (!data || (data && !data.total_count))
                  ? <EmptyBox title="Нет данных" description={!!this.state.search && 'Поиск не дал результатов'} />
                  : (
                    <InfiniteScroll
                      dataLength={Number(data.list.length) || 0}
                      next={() => this.getNext(data.total_pages)}
                      hasMore={this.state.hasMore}
                      loader={null}
                    >
                      {data.list.map(partner => (
                        <PartnerCard
                          key={partner.id}
                          partner={partner}
                          to={`/organizations/${partner.id}`}
                          className="org-partner-statistics-page__item"
                        />
                      ))}
                    </InfiniteScroll>
                  )}
            </div>
          </div>
        </div>

        <MobileMenu
          isOpen={this.state.showMenu}
          contentLabel="Параметры даты"
          onRequestClose={() => this.setState({ ...this.state, showMenu: false })}
        >
          <MenuDatePicker
            start={this.state.start}
            end={this.state.end}
            onChange={range => {
              this.setState({ ...this.state, ...range, page: 1, hasMore: true, showMenu: false });
              this.props.getOrgPartnerStatisticSummary(this.organization, range);
              this.props.getOrgPartners(this.organization,{
                ...this.state,
                ...range,
                page: 1,
              });
            }}
          />
        </MobileMenu>
      </div>
    );
  }
}

const mapStateToProps = state => ({
  orgPartnersSummary: state.statisticStore.orgPartnersSummary,
  orgPartners: state.partnerStore.orgPartners,
})

const mapDispatchToProps = dispatch => ({
  getOrgPartners: (orgID, params, isNext) => dispatch(getOrgPartners(orgID, params, isNext)),
  getOrgPartnerStatisticSummary: (orgID, params) => dispatch(getOrgPartnerStatisticSummary(orgID, params)),
})

export default connect(mapStateToProps, mapDispatchToProps)(OrgPartnerStatisticsPage);