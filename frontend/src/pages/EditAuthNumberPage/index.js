import React, {Component} from 'react';
import {connect} from 'react-redux';
import {setAuthChangeCode} from '../../store/actions/commonActions';
import VerifyForm from '../../components/Forms/VerifyForm';
import AuthForm from '../../components/Forms/AuthForm';
import {RESEND_TYPES} from '../../common/constants';
import {
  changeAuthNumber,
  getUserLocation, resendCode,
  sendCodeToNewNumber,
  validateOldNumber,
  verifyCode
} from '../../store/actions/userActions';
import './index.scss';

class EditAuthNumberPage extends Component {
  componentDidMount() {
    const { code } = this.props.match.params;
    if (code !== this.props.authChangeCode) {
      return this.props.history.push('/profile/edit')
    }

    this.props.getUserLocation();
    this.props.validateOldNumber();
  }

  componentWillUnmount() {
    this.props.setAuthChangeCode(null);
  }

  constructor(props) {
    super(props);
    this.state = {
      phone: null,
      step: 0
    }
  }

  setStep = (step, phone) => this.setState({ ...this.state, phone, step });

  onFirstVerify = async ({ code }) => {
    const { user, verifyCode } = this.props;
    if (user && user.phone_number) {
      const res = await verifyCode(user.phone_number, code.join(''));
      if (res && res.token) {
        return this.setStep(1)
      }
    }
  }

  onPhoneSubmit = async ({ phoneNumber }) => {
    const phone = `+${phoneNumber}`;
    const res = await this.props.sendCodeToNewNumber(phone);
    if (res && res.success) {
      return this.setStep(2, phone);
    }
  }

  onLastVerify = async ({ code }) => {
    const { user, changeAuthNumber, history } = this.props;
    if (user && user.phone_number && this.state.phone) {
      const res = await changeAuthNumber({
        old_phone_number: user.phone_number,
        new_phone_number: this.state.phone,
        code: code.join('')
      });

      if (res && res.success) {
        return history.push('/profile/edit');
      }
    }
  }

  onResendCode = () => {
    this.state.phone && this.props.resendCode(this.state.phone, RESEND_TYPES.changeAuth);
  }

  render() {
    const { history, user, userLocation } = this.props;

    return (
      <div className="edit-auth-number-page">
        <div className="container">
          {this.state.step === 0 && (
            <VerifyForm
              onSubmit={this.onFirstVerify}
              onBack={() => history.push('/profile/edit')}
              onResend={this.props.validateOldNumber}
              phone={user.phone_number || '----------'}
              email={user.email || '---------'}
              showPhone={user.phone_number}
            />
          )}

          {this.state.step === 1 && (
            <AuthForm
              title="Введите новый номер телефона"
              setStep={() => this.setStep(0)}
              onSubmit={this.onPhoneSubmit}
              userLocation={userLocation}
            />
          )}

          {this.state.step === 2 && (
            <VerifyForm
              onSubmit={this.onLastVerify}
              onBack={() => this.setStep(1)}
              onResend={this.onResendCode}
              phone={this.state.phone || '----------'}
              showPhone={true}
            />
          )}
        </div>
      </div>
    );
  }
}

const mapStateToProps = state => ({
  user: state.userStore.user,
  authChangeCode: state.commonStore.authChangeCode,
  userLocation: state.userStore.userLocation
});

const mapDispatchToProps = dispatch => ({
  setAuthChangeCode: code => dispatch(setAuthChangeCode(code)),
  getUserLocation: () => dispatch(getUserLocation()),
  validateOldNumber: () => dispatch(validateOldNumber()),
  verifyCode: (phoneNumber, code) => dispatch(verifyCode(phoneNumber, code)),
  sendCodeToNewNumber: phoneNumber => dispatch(sendCodeToNewNumber(phoneNumber)),
  changeAuthNumber: payload => dispatch(changeAuthNumber(payload)),
  resendCode: (phoneNumber, type) => dispatch(resendCode(phoneNumber, type)),
});

export default connect(mapStateToProps, mapDispatchToProps)(EditAuthNumberPage);