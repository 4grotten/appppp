import React from 'react';
import {connect} from 'react-redux';
import MobileSearchHeader from '../../components/MobileSearchHeader';
import Preloader from '../../components/Preloader';
import ReceiptCard from '../../components/Cards/ReceiptCard';
import {getOrgReceipts} from '../../store/actions/organizationActions';
import {getOrgStatisticSummary} from '../../store/actions/statisticActions';
import EmptyBox from '../../components/EmptyBox';
import SavingsBlock from '../../components/UI/SavingsBlock';
import * as moment from 'moment';
import {DATE_FORMAT_DD_MMMM_YYYY} from '../../common/constants';
import MobileMenu from '../../components/MobileMenu';
import MenuDatePicker from '../../components/MenuDatePicker';
import InfiniteScroll from 'react-infinite-scroll-component';
import './index.scss';

const DEFAULT_LIMIT = 10;

class OrgReceiptsPage extends React.Component {
  constructor(props) {
    super(props);
    this.organizationID = props.match.params.id;
    this.state = {
      page: 1,
      organization: this.organizationID,
      limit: DEFAULT_LIMIT,
      hasMore: true,
      showMenu: false,
      search: '',
      start: null,
      end: null,
    }
  }

  componentDidMount() {
    this.props.getOrgReceipts(this.state);
    this.props.getOrgStatisticSummary(this.organizationID, {
      start: this.state.start,
      end: this.state.end
    });
  }

  getNext = totalPages => {
    if (this.state.page < totalPages) {
      const nextPage = this.state.page + 1
      this.props.getOrgReceipts({
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
      this.props.getOrgReceipts({ ...this.state, search: value, page: 1 });
    }
  }

  onSearchCancel = () => {
    if (this.state.search !== '') {
      this.setState({ ...this.state, search: '', hasMore: true });
      this.props.getOrgReceipts({ ...this.state, search: '', page: 1 });
    }
  };

  render() {
    const { orgReceipts, history, orgSummary } = this.props;
    const { page, start, end, search } = this.state;
    const { data, loading } = orgReceipts;

    return (
      <div className="org-receipts-page">
        <MobileSearchHeader
          onBack={() => history.goBack()}
          title="Продажи и скидки"
          searchPlaceholder="Поиск по номеру чека"
          searchValue={search}
          onSearchChange={this.onSearchChange}
          onSearchCancel={this.onSearchCancel}
        />

        <div className="org-receipts-page__content">
          <div className="org-receipts-page__top" onClick={() => this.setState({ ...this.state, showMenu: true })}>
            <div className="container">
              <SavingsBlock
                total={orgSummary && orgSummary.total_spent}
                savings={orgSummary && orgSummary.total_savings}
                currency={orgSummary && orgSummary.currency}
                className="org-receipts-page__summary"
              />
              <div className="statistics-page__calendar f-14 f-500" >
                {(start && end)
                  ? `с ${moment(start).locale('ru').format(DATE_FORMAT_DD_MMMM_YYYY)} - по ${moment(end).locale('ru').format(DATE_FORMAT_DD_MMMM_YYYY)}`
                  : 'За все время'
                }
              </div>
            </div>
          </div>

          <div className="org-receipts-page__list">
            <div className="container">
              {(page === 1 && loading)
                ? <Preloader />
                : (!data || (data && !data.total_count))
                  ? <EmptyBox title="Проведенных скидок нет" />
                  : (
                    <InfiniteScroll
                      dataLength={Number(data.list.length) || 0}
                      next={() => this.getNext(data.total_pages)}
                      hasMore={this.state.hasMore}
                      loader={null}
                    >
                      {data.list.map(receipt => (
                        <ReceiptCard
                          key={receipt.id}
                          receipt={receipt}
                          organization={this.organizationID}
                          to={`/organizations/${this.organizationID}/receipts/${receipt.id}`}
                          className="org-receipts-page__item"
                        />
                      ))}
                    </InfiniteScroll>
                  )}
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
                this.props.getOrgStatisticSummary(this.organizationID, range);
                this.props.getOrgReceipts({
                  ...this.state,
                  ...range,
                  page: 1
                });
              }}
            />
          </MobileMenu>
        </div>
      </div>
    )
  }
}

const mapStateToProps = state => ({
  orgSummary: state.statisticStore.orgSummary,
  orgDetail: state.organizationStore.orgDetail,
  orgReceipts: state.organizationStore.orgReceipts,
})

const mapDispatchToProps = dispatch => ({
  getOrgReceipts: (params, isNext) => dispatch(getOrgReceipts(params, isNext)),
  getOrgStatisticSummary: (id, params) => dispatch(getOrgStatisticSummary(id, params)),
})

export default connect(mapStateToProps, mapDispatchToProps)(OrgReceiptsPage);