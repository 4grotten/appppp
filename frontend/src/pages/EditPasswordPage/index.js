import React from 'react';
import {Formik} from 'formik';
import {connect} from 'react-redux';
import {PasswordField} from '../../components/UI/PasswordField';
import Button from '../../components/UI/Button';
import {changePassword} from '../../store/actions/userActions';
import * as Yup from 'yup';
import {ERROR_MESSAGES} from '../../common/messages';
import MobileTopHeader from '../../components/MobileTopHeader';
import './index.scss';

const VALIDATION_SCHEMA = Yup.object().shape({
  oldPassword:  Yup.string().min(6, ERROR_MESSAGES.password_min).required(ERROR_MESSAGES.password_empty),
  newPassword:  Yup.string().min(6, ERROR_MESSAGES.password_min).required(ERROR_MESSAGES.password_empty),
  confirmPassword: Yup.string().min(6, ERROR_MESSAGES.password_min).required(ERROR_MESSAGES.password_empty)
});

class EditPasswordPage extends React.Component {
  onSubmit = async ({ oldPassword, newPassword, confirmPassword }, formikBag) => {
    if (newPassword !== confirmPassword) {
      return formikBag.setFieldError('confirmPassword', ERROR_MESSAGES.password_mismatch)
    }

    const res = await this.props.changePassword({
      old_password: oldPassword,
      new_password: newPassword
    });

    res && res.error === 'Incorrect old password' && formikBag.setFieldError('oldPassword', 'Не верно ввели старый пароль');
    res && res.success === true && this.props.history.push('/profile/edit');
  }

  render() {
    const { history } = this.props;

    return (
      <div className="edit-password-page">
        <div className="container">
          <Formik
            enableReinitialize
            validationSchema={VALIDATION_SCHEMA}
            onSubmit={(values, formikBag) => this.onSubmit(values, formikBag)}
            initialValues={{
              oldPassword: '',
              newPassword: '',
              confirmPassword: '',
            }}
          >
            {({ values, errors, touched, handleChange, handleSubmit}) => (
              <form onSubmit={handleSubmit} className="edit-password-form">
                <MobileTopHeader
                  onBack={() => history.push('/profile/edit')}
                  title="Смена пароля"
                />
                <PasswordField
                  label="Старый пароль"
                  name="oldPassword"
                  value={values.oldPassword}
                  onChange={handleChange}
                  error={errors.oldPassword && touched.oldPassword && errors.oldPassword}
                />
                <PasswordField
                  label="Новый пароль"
                  name="newPassword"
                  value={values.newPassword}
                  onChange={handleChange}
                  error={errors.newPassword && touched.newPassword && errors.newPassword}
                />
                <PasswordField
                  label="Подтвердить новый пароль"
                  name="confirmPassword"
                  value={values.confirmPassword}
                  onChange={handleChange}
                  error={
                    (values.confirmPassword && values.newPassword !== values.confirmPassword && ERROR_MESSAGES.password_mismatch)
                    || (errors.confirmPassword  &&  touched.confirmPassword && errors.confirmPassword)
                  }
                />
                <Button
                  label="Сохранить"
                  type="submit"
                  disabled={!values.oldPassword || !values.newPassword || !values.confirmPassword}
                  className="edit-password-form__submit"
                />
              </form>
            )}
          </Formik>
        </div>
      </div>
    )
  }
}

const mapDispatchToProps = dispatch => ({
  changePassword: payload => dispatch(changePassword(payload))
});

export default connect(null, mapDispatchToProps)(EditPasswordPage);