import React from 'react';
import {connect} from 'react-redux';
import InfiniteScroll from 'react-infinite-scroll-component';
import MobileSearchHeader from '../../components/MobileSearchHeader';
import {HeaderNav} from '../../components/HeaderNav';
import Button from '../../components/UI/Button';
import ScanView from '../../containers/ScanView';
import {getEmployeeInfo, getEmployees} from '../../store/actions/employeeActions';
import {BackArrow} from '../../components/UI/Icons';
import {QR_PREFIX} from '../../common/constants';
import EmployeeCard from '../../components/Cards/EmployeeCard';
import Preloader from '../../components/Preloader';
import EmptyBox from '../../components/EmptyBox';
import './index.scss';

const DEFAULT_LIMIT = 10;

class EmployeesPage extends React.Component {
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
      limit: DEFAULT_LIMIT,
      hasMore: true,
      search: '',
    }
  }

  componentDidMount() {
    this.props.getEmployees(this.state);
  }

  getNext = totalPages => {
    if (this.state.page < totalPages) {
      const nextPage = this.state.page + 1
      this.props.getEmployees({
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
      this.props.getEmployees({ ...this.state, search: value, page: 1 });
    }
  }

  onSearchCancel = () => {
    if (this.state.search !== '') {
      this.setState({ ...this.state, search: '', hasMore: true });
      this.props.getEmployees({ ...this.state, search: '', page: 1 });
    }
  };

  render() {
    const { page, step, search, organization } = this.state;
    const { employees, history, getEmployeeInfo } = this.props;
    const { data, loading } = employees;

    return (
      <div className="employees-page">
        {step === 0 && (
          <React.Fragment>
            <MobileSearchHeader
              onBack={() => history.push(`/organizations/${organization}`)}
              searchValue={search}
              onSearchChange={this.onSearchChange}
              onSearchCancel={this.onSearchCancel}
              renderHeader={() => <HeaderNav routes={this.routes} />}
              searchPlaceholder="Поиск по ID, ФИО, номеру сотрудника"
            />

            <div className="container">
              <div className="employees-page__content">
                <div className="employees-page__content-top">
                  {(page === 1 && loading)
                    ?  <Preloader />
                    : (!data || (data && !data.total_count))
                      ? <EmptyBox title="Нет сотрудников" description={!!search && 'Поиск не дал результатов'} />
                      : (
                        <InfiniteScroll
                          dataLength={Number(data.list.length) || 0}
                          next={() => this.getNext(data.total_pages)}
                          hasMore={this.state.hasMore}
                          loader={null}
                        >
                          {data.list.map(employee => (
                            <EmployeeCard
                              key={employee.id}
                              employee={employee}
                              className="employees-page__card"
                              active={true}
                            />
                          ))}
                        </InfiniteScroll>
                      )}
                </div>
                <div className="employees-page__content-bottom">
                  <Button
                    label="Пригласить сотрудника"
                    onClick={() => this.setState({ ...this.state, step: 1 })}
                    className="employees-page__invite"
                  />
                </div>
              </div>
            </div>
          </React.Fragment>
        )}

        {step === 1 && (
          <ScanView
            onError={() => null}
            onScan={async userID => {
              if (userID && userID.includes(QR_PREFIX)) {
                const res = await getEmployeeInfo(userID.replace(QR_PREFIX, ''));
                res && res.success && history.push('employees/add')
              }
            }}
            onInputSubmit={async val => {
              if (val) {
                const res = await getEmployeeInfo(val);
                res && res.success && history.push('employees/add')
              }
            }}
          >
            <button
              type="button"
              onClick={() => this.setState({ ...this.state, step: 0 })}
              className="discount-proceed-form__rounded-btn"
            >
              <BackArrow />
            </button>
          </ScanView>
        )}
      </div>
    );
  }
}

const mapStateToProps = state => ({
  employees: state.employeeStore.employees,
})

const mapDispatchToProps = dispatch => ({
  getEmployees: (params, isNext) => dispatch(getEmployees(params, isNext)),
  getEmployeeInfo: id => dispatch(getEmployeeInfo(id)),
})

export default connect(mapStateToProps, mapDispatchToProps)(EmployeesPage);