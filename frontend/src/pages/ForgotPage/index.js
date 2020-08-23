import * as React from 'react'
import VerifyForm from '../../components/Forms/VerifyForm';
import AuthForm from '../../components/Forms/AuthForm';
import {connect} from 'react-redux';
import LoginForm from '../../components/Forms/LoginForm';
import Notify from '../../components/Notification';
import {
  forgotPassword,
  getUserLocation,
  resendCode,
  setPassword,
  verifyCode
} from '../../store/actions/userActions';
import './index.scss';

class ForgotPage extends React.Component {
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
    const res = await this.props.forgotPassword(phone);
    res && !res.error && this.setStep(1, phone);
  }

  onVerify = async ({code}) => {
    if (this.state.phone) {
      const res = await this.props.verifyCode(this.state.phone, code.join(''))
      if (res && res.token) {
        return this.setStep(2);
      }
    }
  }

  onResendCode = () => {
    this.state.phone && this.props.resendCode(this.state.phone);
  }

  onPasswordSubmit = async ({password}, { setFieldError }) => {
    const res = await this.props.setPassword(password);
    if (res && res.success) {
      Notify.success({text: 'Вы успешно сменили пароль'})
      return this.props.history.push('/profile')
    }

    if (res && res.error) {
      return setFieldError('password', res.error)
    }
  }

  render() {
    const { userLocation, history } = this.props;
    return (
      <div className="forgot-page">
        {this.state.step === 0 && <AuthForm onSubmit={this.onPhoneSubmit} userLocation={userLocation} setStep={() => history.goBack()} title="Введите номер телефона" />}
        {this.state.step === 1 && <VerifyForm onSubmit={this.onVerify} onResend={this.onResendCode} onBack={() => this.setStep(0)} phone={this.state.phone} />}
        {this.state.step === 2 && <LoginForm onSubmit={this.onPasswordSubmit} setStep={() => this.setStep(1)} title="Создать новый пароль" />}
      </div>
    )
  }
}

const mapStateToProps = state => ({
  userLocation: state.userStore.userLocation
});

const mapDispatchToProps = dispatch => ({
  getUserLocation: () => dispatch(getUserLocation()),
  resendCode: phoneNumber => dispatch(resendCode(phoneNumber)),
  verifyCode: (phoneNumber, code) => dispatch(verifyCode(phoneNumber, code)),
  setPassword: password => dispatch(setPassword(password)),
  forgotPassword: phone => dispatch(forgotPassword(phone))
});


export default connect(mapStateToProps, mapDispatchToProps)(ForgotPage);