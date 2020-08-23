import React from 'react';
import {Formik} from 'formik';
import ScanView from '../../../containers/ScanView';
import {BackArrow} from '../../UI/Icons';
import MobileTopHeader from '../../MobileTopHeader';
import OrganizationHeader from '../../OrganizationHeader';
import {InputTextField} from '../../UI/InputTextField';
import {padNumber} from '../../../common/utils';
import StandardSelect from '../../UI/StandardSelect';
import Button from '../../UI/Button';
import {DECIMAL_DIGITS, ONLY_DIGITS} from '../../../common/helpers';
import {DEFAULT_EMPTY, QR_PREFIX} from '../../../common/constants';
import * as Yup from 'yup';
import {ERROR_MESSAGES} from '../../../common/messages';
import './index.scss';

const VALIDATION_SCHEMA = Yup.object().shape({
  data: Yup.mixed().required(''),
  amount: Yup.number().min(0, 'Сумма не может быть меньше 0').required(ERROR_MESSAGES.amount_empty),
});

class DiscountProceedForm extends React.Component {

  calculateSavings = (amount, percent) => {
    const percentage = Number(percent);
    return !(isNaN(amount) || isNaN(percentage))
      ? (amount * percentage) / 100
      : 0
  }

  render() {
    const { onSubmit, preprocessDiscount, preOrganization, history } = this.props;

    return (
      <Formik
        enableReinitialize
        validationSchema={VALIDATION_SCHEMA}
        onSubmit={(values, formikBag) => onSubmit(values, formikBag)}
        initialValues={{
          data: null,
          amount: '',
          sourceCard: null,
          percent: 0,
          card: DEFAULT_EMPTY,
          manualPercent: '',
          step: 0
        }}
      >
        {(formikBag) => {
          const { values, setValues, setFieldValue, errors, touched, isSubmitting, handleSubmit } = formikBag;
          const { data } = values;
          const options = [];

          if (data && data.cumulative) {
            options.push({
              value: `${data.cumulative.percent}:${data.cumulative.id}`,
              label: `Накопительная ${data.cumulative.percent}%`
            })
          }

          data && data.fixed.map(card => options.push({value: `${card.percent}:${card.id}`, label: `${card.percent}%`}));

          const amount = Number(values.amount);
          const savings = this.calculateSavings(amount,
            (!!Number(values.manualPercent) && values.manualPercent) || values.percent);
          const total = !isNaN(amount) && parseFloat((amount - savings).toFixed(2));

          return (
            <form className="discount-proceed-form" onSubmit={handleSubmit}>
              {values.step === 0 && (
                <ScanView
                  onError={(err) => console.warn(err)}
                  onInputSubmit={async val => {
                    if (val) {
                      const res = await preprocessDiscount(val);
                      if (res && res.success) {
                        setValues({
                          ...values,
                          data: res.data,
                          userID: val,
                          step: 1
                        })
                      }
                    }
                  }}
                  onScan={async userID => {
                    if (userID && userID.includes(QR_PREFIX)) {
                      const res = await preprocessDiscount(userID.replace(QR_PREFIX, ''));
                      if (res && res.success) {
                        setValues({
                          ...values,
                          data: res.data,
                          userID: userID,
                          step: 1
                        })
                      }
                    }
                  }}
                >
                  <button type="button" onClick={() => {
                    preOrganization && preOrganization.id
                      ? history.push(`/organizations/${preOrganization.id}`)
                      : history.push('/profile')
                  }} className="discount-proceed-form__rounded-btn">
                    <BackArrow />
                  </button>
                </ScanView>
              )}

              {values.step === 1 && (
                <React.Fragment>
                  <MobileTopHeader
                    title="Провести скидку"
                    onBack={() => {
                      preOrganization && preOrganization.id
                        ? history.push(`/organizations/${preOrganization.id}`)
                        : history.push('/profile')
                    }}
                  />

                  <div className="container">
                  <OrganizationHeader
                    image={preOrganization && preOrganization.image}
                    title={preOrganization && preOrganization.title}
                    types={(preOrganization && preOrganization.types) || []}
                    className="discount-proceed-form__header"
                  />

                  <p className="discount-proceed-form__client f-14">
                    Клиент
                    <span className="f-17 f-500">{(values.data && values.data.client.full_name)}</span>
                  </p>

                  <p className="discount-proceed-form__order f-14">
                    Номер заказа
                    <span className="f-600">{(values.data && padNumber(values.data.transaction_id)) || '0000000'}</span>
                  </p>
                  
                  <InputTextField
                    name="amount"
                    label="Сумма"
                    value={values.amount}
                    className="discount-proceed-form__amount"
                    error={errors.amount && touched.amount && errors.amount}
                    onChange={e => {e.target.value !== '00' && (e.target.value === '' || e.target.value.match(DECIMAL_DIGITS)) && setFieldValue('amount', e.target.value)}}
                  />

                  <div className="discount-proceed-form__row">
                    <StandardSelect
                      name="card"
                      options={options}
                      label="Процент скидки"
                      value={values.card}
                      onChange={e => {
                        if (e.target.value) {
                          const card = e.target.value.split(':');
                          setValues({ ...values, card: e.target.value, percent: parseInt(card[0]), sourceCard: card[1]})
                        }
                      }}
                      className="discount-proceed-form__percent"
                    />

                    <div className="discount-proceed-form__manual">
                      <input
                        max={100}
                        min={0}
                        type="number"
                        name="manualPercent"
                        value={values.manualPercent}
                        onChange={e => {e.target.value !== '00' && (e.target.value === '' || (e.target.value.match(ONLY_DIGITS) && e.target.value <= 100)) && setFieldValue('manualPercent', e.target.value)}}
                        placeholder="0"
                        className="discount-proceed-form__manual-input"
                      />%
                    </div>
                  </div>

                  <div className="discount-proceed-form__dashed row f-15">
                    <span>Калькулятор экономии</span>
                    <span className="f-14">{savings} {preOrganization && preOrganization.currency}</span>
                  </div>

                  <div className="discount-proceed-form__dashed row f-15">
                    <span>Итого со скидкой</span>
                    <b className="f-14">{total || 0} {preOrganization && preOrganization.currency}</b>
                  </div>

                  <Button
                    type="submit"
                    disabled={!values.amount || isSubmitting}
                    label="Провести скидку"
                    onSubmit={handleSubmit}
                    className="discount-proceed-form__submit"
                  />
                  </div>
                </React.Fragment>
              )}
            </form>
          )
        }}
      </Formik>
    );
  }
}

export default DiscountProceedForm;