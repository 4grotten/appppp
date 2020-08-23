import * as React from 'react'
import * as Yup from 'yup';
import {Formik} from 'formik';
import {AuthHeader} from '../../../pages/LoginPage';
import {PasswordField} from '../../UI/PasswordField';
import Button from '../../UI/Button';
import {BackButton} from '../../UI/BackButton';
import {ERROR_MESSAGES} from '../../../common/messages';
import {Link} from 'react-router-dom';
import './index.scss';

const VALIDATION_SCHEMA = Yup.object({
  password: Yup.string().min(6, ERROR_MESSAGES.password_min).required(ERROR_MESSAGES.password_empty)
})

const LoginForm = ({ onSubmit, setStep, title }) => (
  <Formik
    enableReinitialize
    validationSchema={VALIDATION_SCHEMA}
    onSubmit={(values, formikBag) => onSubmit(values, formikBag)}
    initialValues={{
      password: ''
    }}
  >
    {({values, errors, touched, handleSubmit, handleChange, setFieldValue}) => (
      <form className="login-form" onSubmit={handleSubmit}>
        <div className="container">
          <BackButton
            type="button"
            onClick={setStep}
            className="login-form__back-btn"
          />
          <AuthHeader title={title || "Введите пароль"} />
          <PasswordField
            value={values.password}
            onChange={handleChange}
            onClear={() => setFieldValue('password', '')}
            error={errors.password && touched.password && errors.password}
            className="login-form__password"
          />
          {title !== 'Создать новый пароль' && <Link to="/forgot" className="login-form__forgot f-15">Забыли пароль?</Link>}
          <Button
            type="submit"
            label="Дальше"
            onSubmit={handleSubmit}
            className="login-form__button"
          />
        </div>
      </form>
    )}
  </Formik>
)

export default LoginForm;