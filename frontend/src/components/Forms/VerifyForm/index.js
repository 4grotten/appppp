import * as React from 'react'
import * as Yup from 'yup';
import * as classnames from 'classnames';
import {Formik} from 'formik';
import {AuthHeader} from '../../../pages/LoginPage';
import {VerificationCodeInput} from '../../UI/VerificationCodeInput';
import Button from '../../UI/Button';
import {BackButton} from '../../UI/BackButton';
import './index.scss';

const VALIDATION_SCHEMA = Yup.object({
  code: Yup.array().required('Verification code is required')
})

const CODE_LENGTH = 6;

const VerifyForm = ({ onSubmit, onResend, phone, onBack, showPhone, email }) => (
  <Formik
    enableReinitialize
    validationSchema={VALIDATION_SCHEMA}
    onSubmit={(values, formikBag) => onSubmit(values, formikBag)}
    initialValues={{
      code: [],
      codeSent: false
    }}
  >
    {({values, handleSubmit, setFieldValue}) => (
      <form className={classnames("verify-form", (values.codeSent || showPhone) && "verify-form__code-sent")} onSubmit={handleSubmit}>
        <div className="container">
          <BackButton onClick={onBack} />
          <AuthHeader
            title="Код подтверждения"
            logoDisabled={values.codeSent || showPhone}
            email={email}
          />
          {(values.codeSent || showPhone) && <p className="verify-form__phone">{email ? `Отправлен на ${email} и ${phone}` : `Отправлен на ${phone}`}</p>}
          <div className="verify-form__code-wrap">
            <VerificationCodeInput
              values={values.code}
              className="verify-form__code"
              onChange={value => setFieldValue('code', value.split(''))}
              onComplete={value => {
                setFieldValue('code', value.split(''))
                handleSubmit();
              }}
            />
          </div>
          {!values.codeSent ? (
            <p className="verify-form__resend" onClick={() => {
              setFieldValue('codeSent', true);
              onResend();
            }}>Отправить еще раз код</p>
          ) : (
            <a className="verify-form__resend" href="mailto:support@qrcode.com">Не получили код подтверждения</a>
          )}

          <Button
            className="verify-form__button"
            label="Дальше"
            type="submit"
            onSubmit={handleSubmit}
            disabled={values.code.length !== CODE_LENGTH}
          />
        </div>
      </form>
    )}
  </Formik>
)

export default VerifyForm;