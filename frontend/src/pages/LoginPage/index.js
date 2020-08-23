import * as React from 'react';
import * as moment from 'moment';
import logo from '../../assets/images/logo.png';
import {connect} from 'react-redux';
import AuthForm from '../../components/Forms/AuthForm';
import VerifyForm from '../../components/Forms/VerifyForm';
import LoginForm from '../../components/Forms/LoginForm';
import ProfileForm from '../../components/Forms/ProfileForm';
import {updateProfile} from '../../store/actions/profileActions';
import {uploadFile} from '../../store/actions/commonActions';
import {DATE_FORMAT_YYYY_MM_DD, RESEND_TYPES} from '../../common/constants';
import Notify from '../../components/Notification';
import {
  authenticate,
  getUserLocation,
  loginUser,
  resendCode, setPassword,
  verifyCode
} from '../../store/actions/userActions';
import './index.scss'

class LoginPage extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      step: 0,
      phone: undefined
    };
  }

  componentDidMount() {
    this.props.getUserLocation();
  }

  setStep = (step, phone) => this.setState({ ...this.state, phone, step });

  onPhoneSubmit = async ({ phoneNumber }) => {
    const phone = `+${phoneNumber}`;
    const res = await this.props.authenticate(phone);
    if (res) {
      res.is_new_user === true && this.setStep(1, phone);
      res.is_new_user === false && this.setStep(2, phone);
    }
  }

  onVerifyCode = async ({code}) => {
    if (this.state.phone) {
      const res = await this.props.verifyCode(this.state.phone, code.join(''))
      if (res && !res.error) {
        if (res.is_new_user && res.token) {
          return this.setStep(3);
        }
        return this.setStep(2)
      }
    }
  }

  onPasswordEnter = ({ password }, { setFieldError }) => {
    this.state.phone && this.props.loginUser({
      phone_number: this.state.phone,
      password
    }).then(res => {
      if (res && res.is_wrong_psw) {
        setFieldError('password', 'Неверный пароль. Повторите попытку или нажмите на ссылку "Забыли пароль?", чтобы сбросить его.')
      }
    });
  }

  onProfileSubmit = async (data, { setSubmitting, setFieldError }) => {
    try {
      const payload = {
        gender: data.gender,
        username: data.nickname,
        email: data.email,
        full_name: data.fullname,
        date_of_birth: moment(data.birthday).format(DATE_FORMAT_YYYY_MM_DD)
      };

      if (data.croppedAvatar) {
        const res = await this.props.uploadFile(data.croppedAvatar);
        res && res.id && (payload.avatar_id = res.id);
      } else {
        setFieldError('avatar', 'Не удалось обрезать фотографию')
      }

      if (payload.avatar_id) {
        const res = await this.props.updateProfile(payload);
        if (res && res.id) {
          const res = await this.props.setPassword(data.password);
          if (res && res.success) {
            Notify.success({ text: 'Профиль успешно создан'})
            return this.props.history.push('/home');
          }
        }
      }
      setSubmitting(false);
    } catch (e) {}
  }

  onResendCode = () => {
    this.state.phone && this.props.resendCode(this.state.phone, RESEND_TYPES.registration);
  }

  render() {
    const { userLocation, location } = this.props;
    return (
      <div className="login-page">
        {this.state.step === 0 && <AuthForm onSubmit={this.onPhoneSubmit} userLocation={userLocation} path={location.pathname} />}
        {this.state.step === 1 && <VerifyForm onSubmit={this.onVerifyCode} onBack={() => this.setStep(0)} onResend={this.onResendCode} phone={this.state.phone} />}
        {this.state.step === 2 && <LoginForm onSubmit={this.onPasswordEnter} setStep={() => this.setStep(0)} />}
        {this.state.step === 3 && <ProfileForm onSubmit={this.onProfileSubmit} setStep={this.setStep} />}
      </div>
    )
  }
}

const mapStateToProps = state => ({
  user: state.userStore.user,
  token: state.userStore.token,
  userLocation: state.userStore.userLocation
});

const mapDispatchToProps = dispatch => ({
  authenticate: phoneNumber => dispatch(authenticate(phoneNumber)),
  verifyCode: (phoneNumber, code) => dispatch(verifyCode(phoneNumber, code)),
  resendCode: (phoneNumber, type) => dispatch(resendCode(phoneNumber, type)),
  updateProfile: data => dispatch(updateProfile(data)),
  uploadFile: file => dispatch(uploadFile(file)),
  loginUser: payload => dispatch(loginUser(payload)),
  setPassword: password => dispatch(setPassword(password)),
  getUserLocation: () => dispatch(getUserLocation())
});

export default connect(mapStateToProps, mapDispatchToProps)(LoginPage);

export const AuthHeader = ({title, showAppName, logoDisabled}) => (
  <React.Fragment>
    <h1 className="login-page__title">{title}</h1>
    {!logoDisabled && (
      <div className="login-page__image">
        <div className="login-page__logo">
          <img src={logo} alt="QR Plus Logo" />
        </div>
      </div>
    )}
    {showAppName && <p className="login-page__app-name">APOFIZ</p>}
  </React.Fragment>
)