import React from 'react';
import moment from 'moment';
import MobileTopHeader from '../../components/MobileTopHeader';
import SingleCalendar from '../../components/UI/AttendanceCalendar';
import {DATE_FORMAT_DD_MMMM_YYYY, DATE_FORMAT_MMMM_YYYY, DATE_FORMAT_YYYY_MM} from '../../common/constants';
import UserCard from '../../components/Cards/UserCard';
import {connect} from 'react-redux';
import {getAttendanceStatus} from '../../store/actions/attendanceActions';
import Preloader from '../../components/Preloader';
import {AttendanceInIcon, AttendanceOutIcon} from '../../components/UI/Icons';
import './index.scss';

class AttendancePage extends React.Component {
  constructor(props) {
    super(props);
    this.organization = props.match.params.id;
    this.employeeID = props.match.params.employeeID;

    this.state = {
      date: new Date(),
      dateTitle: moment().locale('ru-RU').format(DATE_FORMAT_MMMM_YYYY),
      selected: null
    }
  }

  componentDidMount() {
    this.getAttendances(this.state.date, true);
  }

  getAttendances = (date, isSet) => {
    this.props.getAttendanceStatus(this.employeeID, { month_year: moment(date).format(DATE_FORMAT_YYYY_MM) }).then(res =>
      res &&
      res.success &&
      isSet && this.setState({ ...this.state, selected: this.getAttendanceInfo()[0]})
    )
  }

  getAttendanceInfo = date => {
    const { data } = this.props.attendanceStatus;
    return data.calendar ? data.calendar.filter(item => moment(item.date).isSame(date || this.state.date, 'day')) : []
  }

  onDateChange = date => {
    this.setState({ ...this.state, date, selected: this.getAttendanceInfo(date)[0] });
  }

  onViewChange = date => {
    this.onDateTitleUpdate(moment(date).locale('ru-RU').format(DATE_FORMAT_MMMM_YYYY));
    this.getAttendances(date);
  }

  onDateTitleUpdate = title => {
    this.setState({ ...this.state, dateTitle: title });
  }

  render() {
    const { date, selected, dateTitle } = this.state;
    const { attendanceStatus } = this.props;
    const { data, loading } = attendanceStatus;
    const { history } = this.props;

    if (!data) {
      return null;
    }

    const lastIndex = (selected && selected.attendances.length - 1) || 0;

    return (
      <div className="attendance-page">
        <MobileTopHeader
          onBack={() => history.push(`/organizations/${this.organization}/employees/${this.employeeID}`)}
          title={dateTitle}
        />
        <div className="attendance-page__calendar">
          <div className="container">
            <SingleCalendar
              value={date}
              onChange={this.onDateChange}
              onViewChange={this.onViewChange}
              calendar={data.calendar}
              disableHeader
            />
          </div>
        </div>

        <div className="container">
        {loading ? !data && <Preloader /> : data && (
          <React.Fragment>
            <UserCard
              avatar={data.employee && data.employee.avatar}
              fullname={data.employee.full_name}
              description={data.employee.role}
              className="attendance-page__user"
              withBorder
            />

            <h2 className="attendance-page__current-date f-20 f-800">{moment(date).locale('ru-RU').format(DATE_FORMAT_DD_MMMM_YYYY)}</h2>

            {!selected ? (
              <div className="attendance-page__excepted">
                <AttendanceInIcon />
                <p className="f-16 f-500">Не было</p>
              </div>
            ) : (
              <div className="attendance-page__statuses">
                <div className="attendance-page__status">
                  <div className="attendance-page__status-top row">
                    <AttendanceInIcon />
                    <div className="attendance-page__status-time in f-17 f-600">{moment(selected.attendances[lastIndex].arrival_time).format('hh:mm')}</div>
                  </div>
                  <div className="attendance-page__bottom">
                    <p className="f-11">{selected.attendances[lastIndex].arrival_checked_by ? 'Охрана:' : 'Система:'}</p>
                    <p className="attendance-page__status-user f-12">{selected.attendances[lastIndex].arrival_checked_by ? selected.attendances[lastIndex].arrival_checked_by.full_name : ''}</p>
                  </div>
                </div>
                <div className="attendance-page__status">
                  <div className="attendance-page__status-top row">
                    <AttendanceOutIcon />
                    <div className="attendance-page__status-time out f-17 f-600">
                      {
                        selected.attendances[lastIndex] && selected.attendances[lastIndex].departure_time
                          ? selected.attendances[lastIndex].departure_checked_by ? moment(selected.attendances[lastIndex].departure_time).format('hh:mm') : moment(selected.attendances[lastIndex].departure_time).utc().format('hh:mm')
                          : '--:--'
                      }
                    </div>
                  </div>
                  <div className="attendance-page__bottom">
                    <p className="f-11">{selected.attendances[lastIndex] && selected.attendances[lastIndex].departure_checked_by ? 'Охрана:' : 'Система:'}</p>
                    <p className="attendance-page__status-user f-12">
                      {
                        selected.attendances[lastIndex] && selected.attendances[lastIndex].departure_time
                          ? selected.attendances[lastIndex].departure_checked_by ? selected.attendances[lastIndex].departure_checked_by.full_name : 'Автоматический выход'
                          : 'На работе'
                      }
                    </p>
                  </div>
                </div>
              </div>
            )}
          </React.Fragment>
        )}
        </div>
      </div>
    );
  }
}

const mapStateToProps = state => ({
  attendanceStatus: state.attendanceStore.attendanceStatus,
})

const mapDispatchToProps = dispatch => ({
  getAttendanceStatus: (employeeID, params) => dispatch(getAttendanceStatus(employeeID, params)),
})

export default connect(mapStateToProps, mapDispatchToProps)(AttendancePage);