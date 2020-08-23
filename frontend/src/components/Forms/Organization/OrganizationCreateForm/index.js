import React, {Component} from 'react';
import {Formik} from 'formik';
import {
  DEFAULT_END_H,
  DEFAULT_END_M,
  DEFAULT_START_H,
  DEFAULT_START_M
} from '../../../UI/TimeRangeField';
import MainView from '../main';
import ContactsView from '../contacts';
import NetworksView from '../networks';
import DiscountView from '../discount';
import OrganizationTypesView from '../../../../containers/OrganizationTypesView';
import OrganizationSubTypesView from '../../../../containers/OrganizationSubTypesView';
import CurrencyView from '../../../../containers/CurrencyView';
import {ERROR_MESSAGES} from '../../../../common/messages';
import * as Yup from 'yup';
import MapView from '../../../../containers/MapView';
import {validateForSameDiscount} from '../../../../common/helpers';
import Notify from '../../../Notification';

const VALIDATION_SCHEMA = Yup.object().shape({
  image: Yup.mixed().required(ERROR_MESSAGES.image_empty),
  country: Yup.mixed().required(ERROR_MESSAGES.currency_empty),
  title: Yup.string().required('Укажите название организации'),
  // address: Yup.string().required('Укажите адрес организации'),
  description: Yup.string().required('Укажите описание организации'),
  openAt: Yup.string().required('Укажите время начало работы'),
  closeAt: Yup.string().required('Укажите время начало работы'),
  numbers: Yup.array().of(
    Yup.object().shape({
      id: Yup.string().required(),
      phone_number: Yup.string().min(4, ERROR_MESSAGES.phone_empty).required(ERROR_MESSAGES.phone_empty)
    })
  ),
  socials: Yup.array().of(
    Yup.object().shape({
      id: Yup.string().required(),
      url: Yup.string().required(ERROR_MESSAGES.social_empty)
    })
  ),
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
  ),
  selectedTypes: Yup.array().of(
    Yup.object().shape({
      id: Yup.string().required()
    })
  ).required('Укажите вид организации')
});

class OrganizationForm extends Component {
  onTypeSelect = (selected, current, setFieldValue) => {
    let isNew = true;
    let filtered = current.filter(item => {
      if (item.id === selected.id) {
        isNew = false;
        return false;
      }
      return true;
    })
    isNew && filtered.length < 3 && filtered.push(selected);
    isNew && current.length === 3 && Notify.success({ text: 'Можно выбрать не более 3 сфер видов организации' });
    setFieldValue('selectedTypes', filtered);
  }

  render() {
    const { onSubmit, orgTypes, userGEO, history } = this.props;
    return (
      <Formik
        enableReinitialize
        validationSchema={VALIDATION_SCHEMA}
        validate={(values) => {
          const errors = {};
          const accDiscountErrors = validateForSameDiscount(values.accDiscounts);
          if (accDiscountErrors) {
            errors.accDiscounts = accDiscountErrors
          }
          const fixedDiscountErrors = validateForSameDiscount(values.fixedDiscounts);
          if (fixedDiscountErrors) {
            errors.fixedDiscounts = fixedDiscountErrors
          }
          return errors;
        }}
        onSubmit={(values, formikBag) => onSubmit(values, formikBag)}
        initialValues={{
          image: null,
          imageURL: null,
          title: '',
          description: '',
          address: '',
          openAt: [DEFAULT_START_H, DEFAULT_START_M].join(':'),
          closeAt: [DEFAULT_END_H, DEFAULT_END_M].join(':'),
          numbers: [],
          socials: [],
          fixedDiscounts: [],
          accDiscounts: [],
          selectedTypes: [],
          location: null,
          country: {
            code: "KG",
            name: "Кыргызстан",
            flag: "https://github.com/IainMcManus/FlagAndCountryData/blob/master/flags/flags-iso/flat/64/KG.png?raw=True",
            currency: {
              code: "KGS",
              name: "Кыргызский сом"
            }
          },
          selectedCatID: null,
          step: 0
        }}
      >
        {(formikBag) => {
          const { values, setFieldValue, validateForm, setTouched, handleSubmit } = formikBag;
          return (
            <form className="organization-create-form" onSubmit={handleSubmit}>
              {formikBag.values.step === 0 && (
                <MainView
                  formikBag={formikBag}
                  onBack={() => history.push('/profile')}
                  onMap={() => setFieldValue('step', 7)}
                  onNext={async () => {
                    const errors = await validateForm();
                    await setTouched({
                      image: true,
                      imageURL: true,
                      title: true,
                      address: true,
                      country: true,
                      description: true,
                      openAt: true,
                      closeAt: true,
                      numbers: true,
                      socials: true,
                      selectedTypes: true
                    });

                    if (errors && (errors.image || errors.title || errors.description || errors.openAt || errors.closeAt || errors.numbers || errors.socials || errors.selectedTypes)) {
                      return;
                    }

                    setFieldValue('step', 3)
                  }}
                />
              )}

              {formikBag.values.step === 1 && (
                <ContactsView
                  formikBag={formikBag}
                  onBack={() => setFieldValue('step', 0)}
                  onSave={() => setFieldValue('step', 0)}
                />
              )}

              {formikBag.values.step === 2 && (
                <NetworksView
                  formikBag={formikBag}
                  onBack={() => setFieldValue('step', 0)}
                  onSave={() => setFieldValue('step', 0)}
                />
              )}

              {formikBag.values.step === 3 && (
                <DiscountView
                  formikBag={formikBag}
                  onBack={() => setFieldValue('step', 0)}
                />
              )}

              {formikBag.values.step === 4 && (
                <OrganizationTypesView
                  orgTypes={orgTypes}
                  selectedTypes={formikBag.values.selectedTypes}
                  onBack={() => setFieldValue('step', 0)}
                  onSelect={catID => {
                    setFieldValue('selectedCatID', catID);
                    setFieldValue('step', 5);
                  }}
                />
              )}

              {formikBag.values.step === 5 && (
                <OrganizationSubTypesView
                  orgTypes={orgTypes}
                  catID={values.selectedCatID}
                  onBack={() => setFieldValue('step', 4)}
                  onNext={() => setFieldValue('step', 0)}
                  selectedTypes={values.selectedTypes}
                  onSelect={selection => this.onTypeSelect(selection, values.selectedTypes, setFieldValue)}
                />
              )}

              {formikBag.values.step === 6 && (
                <CurrencyView
                  onBack={() => setFieldValue('step', 0)}
                  onChange={(country) => {
                    setFieldValue('country', country);
                    setFieldValue('step', 0);
                  }}
                />
              )}

              {formikBag.values.step === 7 && (
                <MapView
                  onBack={() => setFieldValue('step', 0)}
                  onChange={location => {
                    setFieldValue('location', location);
                    setFieldValue('step', 0);
                  }}
                  editMode
                  position={values.location && [values.location.lat, values.location.lng]}
                  userGEO={userGEO}
                />
              )}
            </form>
          )
        }}
      </Formik>
    );
  }
}

export default OrganizationForm;