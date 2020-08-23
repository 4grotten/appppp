import React from 'react';
import {connect} from 'react-redux';
import MobileSearchHeader from '../../components/MobileSearchHeader';
import Preloader from '../../components/Preloader';
import ReceiptCard from '../../components/Cards/ReceiptCard';
import {getOrgReceipts} from '../../store/actions/organizationActions';
import EmptyBox from '../../components/EmptyBox';
import SavingsBlock from '../../components/UI/SavingsBlock';
import * as moment from 'moment';
import {DATE_FORMAT_DD_MMMM_YYYY} from '../../common/constants';
import {getOrgStatisticSummary} from '../../store/actions/statisticActions';
import InfiniteScroll from 'react-infinite-scroll-component';
import MenuDatePicker from '../../components/MenuDatePicker';
import MobileMenu from '../../components/MobileMenu';
import './index.scss';

const DEFAULT_LIMIT = 10;

class OrgReceiptsByUserPage extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      page: 1,
      organization: props.match.params.id,
      processed_by: props.match.params.userID,
      limit: DEFAULT_LIMIT,
      hasMore: true,
      showMenu: false,
      start: null,
      end: null,
    }
  }

  componentDidMount() {
    const { organization, start, end, processed_by } = this.state;
    if (!organization) { return this.props.history.push(`/profile`); }
    this.props.getOrgReceipts(this.state);
    this.props.getOrgStatisticSummary(organization, { start, end, processed_by });
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

  render() {
    const { orgReceipts, orgReceiptDetail, history, orgSummary } = this.props;
    const { data, loading } = orgReceipts;
    const { page, start, end } = this.state;

    return (
      <div className="org-receipts-user-page">
        <MobileSearchHeader
          onBack={() => history.goBack()}
          title={(orgReceiptDetail.data && orgReceiptDetail.data.processed_by && orgReceiptDetail.data.processed_by.full_name) || 'Пользователь'}
        />

        <div className="org-receipts-user-page__content">
          <div className="org-receipts-user-page__top" onClick={() => this.setState({ ...this.state, showMenu: true })}>
            <div className="container">
              <SavingsBlock
                total={orgSummary && orgSummary.total_spent}
                savings={orgSummary && orgSummary.total_savings}
                currency={orgSummary && orgSummary.currency}
                className="org-receipts-user-page__summary"
              />
              <div className="statistics-page__calendar f-14 f-500" >
                {(start && end)
                  ? `с ${moment(start).locale('ru').format(DATE_FORMAT_DD_MMMM_YYYY)} - по ${moment(end).locale('ru').format(DATE_FORMAT_DD_MMMM_YYYY)}`
                  : 'За все время'
                }
              </div>
            </div>
          </div>

          <div className="org-receipts-user-page__list">
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
                          className="org-receipts-user-page__item"
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
              this.props.getOrgStatisticSummary(this.state.organization, range);
              this.props.getOrgReceipts({
                ...this.state,
                ...range,
                page: 1
              });
            }}
          />
        </MobileMenu>
      </div>
    );
  }
}

const mapStateToProps = state => ({
  orgSummary: state.statisticStore.orgSummary,
  orgDetail: state.organizationStore.orgDetail,
  orgReceipts: state.organizationStore.orgReceipts,
  orgReceiptDetail: state.organizationStore.orgReceiptDetail,
})

const mapDispatchToProps = dispatch => ({
  getOrgReceipts: (params, isNext) => dispatch(getOrgReceipts(params, isNext)),
  getOrgStatisticSummary: (id, params) => dispatch(getOrgStatisticSummary(id, params)),
})

export default connect(mapStateToProps, mapDispatchToProps)(OrgReceiptsByUserPage);