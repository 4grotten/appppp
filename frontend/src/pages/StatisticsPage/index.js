import React from 'react';
import * as moment from 'moment';
import MobileSearchHeader from '../../components/MobileSearchHeader';
import PartnerCard from '../../components/Cards/PartnerCard';
import {connect} from 'react-redux';
import {getAllStatistics, getStatisticSummary} from '../../store/actions/statisticActions';
import InfiniteScroll from 'react-infinite-scroll-component';
import EmptyBox from '../../components/EmptyBox';
import Preloader from '../../components/Preloader';
import SavingsBlock from '../../components/UI/SavingsBlock';
import MobileMenu from '../../components/MobileMenu';
import MenuDatePicker from '../../components/MenuDatePicker';
import {DATE_FORMAT_DD_MMMM_YYYY} from '../../common/constants';
import './index.scss';

const DEFAULT_LIMIT = 10;

class StatisticsPage extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      page: 1,
      limit: DEFAULT_LIMIT,
      hasMore: true,
      showMenu: false,
      start: null,
      end: null,
    }
  }

  componentDidMount() {
    this.props.getAllStatistics(this.state);
    this.props.getStatisticSummary({
      start: this.state.start,
      end: this.state.end
    });
  }

  getNext = totalPages => {
    if (this.state.page < totalPages) {
      const nextPage = this.state.page + 1
      this.props.getAllStatistics({
        ...this.state,
        page: nextPage,
      }, true);

      return this.setState({ ...this.state, hasMore: true, page: nextPage })
    }
    this.setState({ ...this.state, hasMore: false });
  }

  render() {
    const { allStatistics, summary, history } = this.props;
    const { data, loading } = allStatistics;
    const { page, start, end } = this.state;

    return (
      <div className="statistics-page">
        <MobileSearchHeader
          onBack={() => history.goBack()}
          title="Ваша статистика"
        />

        <div className="statistics-page__content">
          <div className="statistics-page__top" onClick={() => this.setState({ ...this.state, showMenu: true })}>
            <div className="container">
              <SavingsBlock
                total={summary && summary.total_spent}
                savings={summary && summary.total_savings}
                currency={summary && summary.currency}
                className="statistics-page__summary"
              />
              <div className="statistics-page__calendar f-14 f-500">
                {(start && end)
                  ? `с ${moment(start).locale('ru').format(DATE_FORMAT_DD_MMMM_YYYY)} - по ${moment(end).locale('ru').format(DATE_FORMAT_DD_MMMM_YYYY)}`
                  : 'За все время'
                }
              </div>
            </div>
          </div>

          <div className="statistics-page__list">
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
                          className="statistics-page__item"
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
              this.props.getStatisticSummary(range);
              this.props.getAllStatistics({
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
  summary: state.statisticStore.summary,
  allStatistics: state.statisticStore.allStatistics,
})

const mapDispatchToProps = dispatch => ({
  getAllStatistics: (params, isNext) => dispatch(getAllStatistics(params, isNext)),
  getStatisticSummary: params => dispatch(getStatisticSummary(params)),
})

export default connect(mapStateToProps, mapDispatchToProps)(StatisticsPage);