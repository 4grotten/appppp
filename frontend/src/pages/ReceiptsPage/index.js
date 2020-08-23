import React from 'react';
import qs from 'qs';
import {connect} from 'react-redux';
import MobileSearchHeader from '../../components/MobileSearchHeader';
import {getOrganizationTitle, getReceipts, getStatisticSummary} from '../../store/actions/statisticActions';
import ReceiptCard from '../../components/Cards/ReceiptCard';
import Preloader from '../../components/Preloader';
import InfiniteScroll from 'react-infinite-scroll-component';
import EmptyBox from '../../components/EmptyBox';
import SavingsBlock from '../../components/UI/SavingsBlock';
import {DATE_FORMAT_DD_MMMM_YYYY} from '../../common/constants';
import * as moment from 'moment';
import MenuDatePicker from '../../components/MenuDatePicker';
import MobileMenu from '../../components/MobileMenu';
import './index.scss';

const DEFAULT_LIMIT = 10;

class ReceiptsPage extends React.Component {
  constructor(props) {
    const { org } = qs.parse(props.location.search.replace('?', ''));
    super(props);
    this.state = {
      page: 1,
      limit: DEFAULT_LIMIT,
      search: '',
      organization: Number(org) || null,
      hasMore: true,
      showMenu: false,
      start: null,
      end: null,
      title: '',
    }
  }

  componentDidMount() {
    const { organization, start, end } = this.state;
    if (organization) {
      this.props.getStatisticSummary({ organization: this.state.organization, start, end });
      this.props.getOrganizationTitle(organization).then(res => {
        res && res.success && this.setState({...this.state, title: res.title});
      });
      return this.props.getReceipts(this.state);
    } else { this.props.history.push('/home') }
  }

  onSearchChange = e => {
    const { value } = e.target;
    if (value !== this.state.search) {
      this.setState({ ...this.state, search: value, page: 1, hasMore: true });
      this.props.getReceipts({ ...this.state, search: value, page: 1 });
    }
  }

  onSearchCancel = () => {
    if (this.state.search !== '') {
      this.setState({ ...this.state, search: '', hasMore: true });
      this.props.getReceipts({ ...this.state, search: '', page: 1 });
    }
  };

  getNext = totalPages => {
    if (this.state.page < totalPages) {
      const nextPage = this.state.page + 1
      this.props.getReceipts({
        ...this.state,
        page: nextPage,
      }, true);

      return this.setState({ ...this.state, hasMore: true, page: nextPage })
    }
    this.setState({ ...this.state, hasMore: false });
  }

  render() {
    const { page, showMenu, start, end, organization, title, search } = this.state;
    const { summary, receipts, history, location } = this.props;
    const { r } = qs.parse(location.search.replace('?', ''));
    const { data, loading } = receipts;

    return (
      <div className="receipts-page">
        <MobileSearchHeader
          onBack={() => !!r ? history.push(`/organizations/${organization}`) : history.push('/statistics')}
          title={title}
          searchValue={search}
          onSearchChange={this.onSearchChange}
          onSearchCancel={this.onSearchCancel}
          searchPlaceholder="Поиск по номеру чека"
        />

        <div className="receipts-page__content">
          <div className="receipts-page__top" onClick={() => this.setState({ ...this.state, showMenu: true })}>
            <div className="container">
              <SavingsBlock
                total={summary && summary.total_spent}
                savings={summary && summary.total_savings}
                currency={summary && summary.currency}
                className="org-receipts-page__summary"
              />
              <div className="receipts-page__calendar f-14 f-500" >
                {(start && end)
                  ? `с ${moment(start).locale('ru').format(DATE_FORMAT_DD_MMMM_YYYY)} - по ${moment(end).locale('ru').format(DATE_FORMAT_DD_MMMM_YYYY)}`
                  : 'За все время'
                }
              </div>
            </div>
          </div>

          <div className="receipts-page__list">
            <div className="container">
              {(page === 1 && loading)
                ?  <Preloader />
                : (!data || (data && !data.total_count))
                  ? <EmptyBox title="Нет чеков" description={!!this.state.search && 'Поиск не дал результатов'} />
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
                          organization={this.state.organization}
                          className="receipts-page__item"
                        />
                      ))}
                    </InfiniteScroll>
                  )}
            </div>
          </div>
        </div>

        <MobileMenu
          isOpen={showMenu}
          contentLabel="Параметры даты"
          onRequestClose={() => this.setState({ ...this.state, showMenu: false })}
        >
          <MenuDatePicker
            start={start}
            end={end}
            onChange={range => {
              this.setState({ ...this.state, ...range, page: 1, hasMore: true, showMenu: false });
              this.props.getStatisticSummary({ organization, ...range });
              this.props.getReceipts({
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
  summary: state.statisticStore.summary,
  receipts: state.statisticStore.receipts,
})

const mapDispatchToProps = dispatch => ({
  getReceipts: (params, isNext) => dispatch(getReceipts(params, isNext)),
  getStatisticSummary: params => dispatch(getStatisticSummary(params)),
  getOrganizationTitle: id => dispatch(getOrganizationTitle(id)),
})

export default connect(mapStateToProps, mapDispatchToProps)(ReceiptsPage);