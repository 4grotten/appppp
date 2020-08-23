import React from 'react';
import {Formik} from 'formik';
import {connect} from 'react-redux';
import ScanView from '../../containers/ScanView';
import {QR_PREFIX} from '../../common/constants';
import {AttendanceInIcon, AttendanceOutIcon, BackArrow} from '../../components/UI/Icons';
import {getEmployeeInfoATD, recordAttendance} from '../../store/actions/attendanceActions';
import MobileTopHeader from '../../components/MobileTopHeader';
import Button from '../../components/UI/Button';
import Avatar from '../../components/UI/Avatar';
import Preloader from '../../components/Preloader';
import './index.scss';

class AttendanceScanPage extends React.Component {
  constructor(props) {
    super(props);
    this.organization = props.match.params.id;
  }

  onSubmit = (values, formikBag) => {
    this.props.recordAttendance({
      user: values.user.id,
      organization: this.organization
    }).then(res => res && res.success && formikBag.setValues({ employee: null, step: 0 }));
  }

  render() {
    const { getEmployeeInfoATD, history } = this.props;

    return (
      <Formik
        onSubmit={this.onSubmit}
        initialValues={{
          user: null,
          step: 0
        }}
      >
        {({ values, setValues, handleSubmit, setFieldValue }) => (
          <form className="attendance-scan-page" onSubmit={handleSubmit} >
            {values.step === 0 && (
              <ScanView
                onBack={() => history.goBack()}
                onError={() => null}
                onScan={async userID => {
                  if (userID && userID.includes(QR_PREFIX)) {
                    const res = await getEmployeeInfoATD({
                      organization: this.organization,
                      user: userID.replace(QR_PREFIX, '')
                    });

                    if (res && res.success) {
                      setValues({
                        ...values,
                        user: res.data,
                        step: 1
                      })
                    }
                  }
                }}
                onInputSubmit={async user => {
                  if (user) {
                    const res = await getEmployeeInfoATD({
                      organization: this.organization,
                      user: user
                    });
                    if (res && res.success) {
                      setValues({
                        ...values,
                        user: res.data,
                        step: 1
                      })
                    }
                  }
                }}
                inputPlaceholder="Поиск по ID сотрудника"
              >
                <button
                  type="button"
                  onClick={() => history.goBack()}
                  className="discount-proceed-form__rounded-btn"
                >
                  <BackArrow />
                </button>
              </ScanView>
            )}

            {values.step === 1 && (
              <React.Fragment>
                <MobileTopHeader
                  onBack={() => setFieldValue('step', 0)}
                  title="Пропуск"
                />

                <div className="container">
                  {!values.user ? <Preloader className="attendance-scan-page__preloader" /> : (
                    <div className="attendance-scan-page__user">
                      <div className="attendance-scan-page__avatar-wrap">
                        <Avatar
                          src={values.user.avatar && values.user.avatar.large}
                          alt={values.user.full_name}
                          className="attendance-scan-page__avatar"
                        />
                      </div>

                      <div className="attendance-scan-page__user-content">
                        <p className="attendance-scan-page__user-id f-14 f-600">ID {values.user.id}</p>
                        <h1 className="attendance-scan-page__user-name f-17 f-500">{values.user.full_name}</h1>
                        <p className="attendance-scan-page__user-role f-16 f-500">{values.user.role}</p>
                      </div>

                      <div className="attendance-scan-page__icon">
                        {values.user.attendance && values.user.attendance.is_active ? <AttendanceOutIcon /> : <AttendanceInIcon />}</div>
                      <div className="attendance-scan-page__text f-16 f-500">Пользователь запрашивает доступ</div>

                      <div className="attendance-scan-page__buttons">
                        <Button
                          label="Запретить"
                          type="button"
                          onClick={()=> history.push(`/organizations/${this.organization}`)}
                          className="attendance-scan-page__button-cancel"
                        />

                        <Button
                          label="Разрешить"
                          type="submit"
                          onSubmit={handleSubmit}
                          className="attendance-scan-page__button-accept"
                        />
                      </div>
                    </div>
                  )}
                </div>
              </React.Fragment>
            )}

          </form>
        )}
      </Formik>
    )
  }
}

const mapStateToProps = state => ({
  employeeInfoATD: state.attendanceStore.employeeInfoATD,
})

const mapDispatchToProps = dispatch => ({
  getEmployeeInfoATD: params => dispatch(getEmployeeInfoATD(params)),
  recordAttendance: payload => dispatch(recordAttendance(payload)),
})

export default connect(mapStateToProps, mapDispatchToProps)(AttendanceScanPage);