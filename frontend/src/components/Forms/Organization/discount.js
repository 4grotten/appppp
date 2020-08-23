import React from 'react';
import MobileTopHeader from '../../MobileTopHeader';
import {DISCOUNT_TYPES} from '../../../common/constants';
import {DiscountIcon} from '../../UI/Icons';
import AccumDiscountForm from '../AccumDiscountForm';
import FixedDiscountForm from '../FixedDiscountForm';

const addDiscount = (type, current, setFieldValue, country) => {
  if (type === DISCOUNT_TYPES.cumulative) {
    setFieldValue('accDiscounts', [...current, {
      id: new Date().toISOString(),
      type: DISCOUNT_TYPES.cumulative,
      percent: '5',
      currency: country && country.currency && country.currency.code || 'KGS',
      limit: '5000'
    }])
  }

  if (type === DISCOUNT_TYPES.fixed) {
    setFieldValue('fixedDiscounts', [...current, {
      id: new Date().toISOString(),
      type: DISCOUNT_TYPES.fixed,
      percent: '10'
    }])
  }
}

const DiscountView = ({ formikBag, onBack }) => {
  const { values, errors, setFieldValue, touched, isSubmitting, handleSubmit } = formikBag;

  return (
    <div className="organization-form-discounts">
      <MobileTopHeader
        title="Скидки"
        onSubmit={handleSubmit}
        disabled={isSubmitting}
        submitLabel={isSubmitting ? 'Сохранение' : 'Сохранить'}
        onBack={onBack}
      />

      <div className="container">
        <div className="organization-form-discounts__header row">
          <h4 className="organization-form-discounts__header-title f-600">Фиксированная карта</h4>
          {!!values.accDiscounts.length && (
            <button
              type="button"
              className="organization-form-discounts__header-add f-14"
              onClick={() => addDiscount(DISCOUNT_TYPES.cumulative, values.accDiscounts, setFieldValue, values.country)}
            >Добавить</button>
          )}
        </div>

        {!values.accDiscounts.length && (
          <button
            type="button"
            onClick={() => addDiscount(DISCOUNT_TYPES.cumulative, values.accDiscounts, setFieldValue, values.country)}
            className="organization-form-discounts__add"
          >
            <DiscountIcon />
            <span className="f-16 f-500">Добавить первую накопительную скидку</span>
          </button>
        )}

        {values.accDiscounts.map((card, index) => (
          <AccumDiscountForm
            key={card.id}
            card={card}
            isEditable={card.is_editable}
            error={errors.accDiscounts && touched.accDiscounts && errors.accDiscounts[index]}
            onRemove={() => {card.is_editable !== false && setFieldValue('accDiscounts', values.accDiscounts.filter((item) => item.id !== card.id))}}
            onChange={card => {setFieldValue('accDiscounts', values.accDiscounts.map(item => item.id === card.id ? card : item))}}
          />
        ))}

        <div className="organization-form-discounts__header row">
          <h4 className="organization-form-discounts__header-title f-600">Акционная карта</h4>
          {!!values.fixedDiscounts.length && (
            <button
              type="button"
              onClick={() => addDiscount(DISCOUNT_TYPES.fixed, values.fixedDiscounts, setFieldValue)}
              className="organization-form-discounts__header-add f-14"
            >
              Добавить
            </button>
          )}
        </div>

        {!values.fixedDiscounts.length && (
          <button
            type="button"
            onClick={() => addDiscount(DISCOUNT_TYPES.fixed, values.fixedDiscounts, setFieldValue)}
            className="organization-form-discounts__add"
          >
            <DiscountIcon />
            <span className="f-16 f-500">Добавить первую фиксированную скидку</span>
          </button>
        )}

        {values.fixedDiscounts.map((card, index) => (
          <FixedDiscountForm
            key={card.id}
            card={card}
            isEditable={card.is_editable}
            error={errors.fixedDiscounts && touched.fixedDiscounts && errors.fixedDiscounts[index]}
            onRemove={() => {setFieldValue('fixedDiscounts', values.fixedDiscounts.filter((item) => item.id !== card.id))}}
            onChange={card => {card.is_editable !== false && setFieldValue('fixedDiscounts', values.fixedDiscounts.map(item => item.id === card.id ? card : item))}}
          />
        ))}
      </div>
    </div>
  );
};

export default DiscountView;