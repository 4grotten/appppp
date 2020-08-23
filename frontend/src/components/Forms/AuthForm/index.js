import * as React from 'react'
import * as Yup from 'yup';
import {Formik} from 'formik';
import {AuthHeader} from '../../../pages/LoginPage';
import Button from '../../UI/Button';
import PhoneInputField from '../../UI/PhoneNumberField';
import {BackButton} from '../../UI/BackButton';
import './index.scss';

const VALIDATION_SCHEMA = Yup.object({
  phoneNumber: Yup
    .string()
    .min(4)
    .required('Введите номер телефона')
})

const AuthForm = ({ onSubmit, setStep, userLocation, path, title }) => (
  <Formik
    enableReinitialize
    validationSchema={VALIDATION_SCHEMA}
    onSubmit={(values, formikBag) => onSubmit(values, formikBag)}
    initialValues={{
      phoneNumber: '',
      countryCode: userLocation && userLocation.countryCode || 'kg'
    }}
  >
    {({values, handleSubmit, setFieldValue, isSubmitting}) => (
      <form className="auth-form" onSubmit={handleSubmit}>
        <div className="container">
          {setStep && <BackButton onClick={setStep} />}
          <AuthHeader
            title={title || "Добро пожаловать"}
            showAppName={path === '/auth'}
          />
          <PhoneInputField
            label="Номер телефона"
            name="phone_number"
            className="auth-form__phone"
            countryCode={values.countryCode}
            value={values.phoneNumber}
            onChange={(phone) => setFieldValue('phoneNumber', phone)}
          />
          <Button
            type="submit"
            label="Дальше"
            disabled={isSubmitting}
            onSubmit={handleSubmit}
            className="auth-form__button"
          />
        </div>
      </form>
    )}
  </Formik>
)

export default AuthForm;