import React, {Component} from 'react';
import {Formik} from 'formik';
import DiscountView from '../discount';
import {validateForSameDiscount} from '../../../../common/helpers';
import {ERROR_MESSAGES} from '../../../../common/messages';
import * as Yup from 'yup';

const VALIDATION_SCHEMA = Yup.object().shape({
  fixedDiscounts: Yup.array().of(
    Yup.object().shape({
      id: Yup.string().required(),
      type: Yup.string().required(),
      percent: Yup.mixed().required(ERROR_MESSAGES.discount_percent_empty)
    })
  ),
  accDiscounts: Yup.array().of(
    Yup.object().shape({
      id: Yup.string().required(),
      type: Yup.string().required(),
      percent: Yup.mixed().required(ERROR_MESSAGES.discount_percent_empty),
      currency: Yup.string().required(),
      limit: Yup.string().required(ERROR_MESSAGES.discount_limit_empty)
    })
  )
});

class OrganizationEditDiscountsForm extends Component {
  render() {
    const { data, onSubmit, history, id } = this.props;

    return (
      <Formik
        validationSchema={VALIDATION_SCHEMA}
        onSubmit={(values, formikBag) => onSubmit(values, formikBag)}
        validate={(values) => {
          const errors = {};
          const accDiscountErrors = validateForSameDiscount(values.accDiscounts, true);
          if (accDiscountErrors) {
            errors.accDiscounts = accDiscountErrors
          }
          const fixedDiscountErrors = validateForSameDiscount(values.fixedDiscounts);
          if (fixedDiscountErrors) {
            errors.fixedDiscounts = fixedDiscountErrors
          }
          return errors;
        }}
        initialValues={{
          fixedDiscounts: data.discounts.fixed,
          accDiscounts: data.discounts.cumulative,
          country: data.country,
        }}
      >
        {(formikBag) => {
          const { handleSubmit } = formikBag;
          return (
            <form className="organization-form" onSubmit={handleSubmit}>
              <DiscountView
                formikBag={formikBag}
                onBack={() => history.push(`/organizations/${id}`)}
              />
            </form>
          )
        }}
      </Formik>
    );
  }
}

export default OrganizationEditDiscountsForm;