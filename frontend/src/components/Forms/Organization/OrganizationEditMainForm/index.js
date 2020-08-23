import React, {Component} from 'react';
import {Formik} from 'formik';
import ContactsView from '../contacts';
import NetworksView from '../networks';
import OrganizationTypesView from '../../../../containers/OrganizationTypesView';
import OrganizationSubTypesView from '../../../../containers/OrganizationSubTypesView';
import CurrencyView from '../../../../containers/CurrencyView';
import {ERROR_MESSAGES} from '../../../../common/messages';
import * as Yup from 'yup';
import MapView from '../../../../containers/MapView';
import MainView from '../main';
import {parseLocation} from '../../../../common/utils';
import RowToggle from '../../../UI/RowToggle';
import RowButton from '../../../UI/RowButton';
import {DeactivateIcon} from '../../../UI/Icons';
import Notify from '../../../Notification';

const VALIDATION_SCHEMA = Yup.object().shape({
  country: Yup.mixed().required(ERROR_MESSAGES.currency_empty),
  title: Yup.string().required('Укажите название организации'),
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
  selectedTypes: Yup.array().of(
    Yup.object().shape({
      id: Yup.string().required()
    })
  ).required('Укажите вид организации')
});

class OrganizationEditMainForm extends Component {
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
    const { data, onSubmit, orgTypes, history, userGEO, id } = this.props;

    return (
      <Formik
        validationSchema={VALIDATION_SCHEMA}
        onSubmit={(values, formikBag) => onSubmit(values, formikBag)}
        initialValues={{
          image: null,
          imageURL: data.image.large,
          title: data.title,
          description: data.description,
          address: data.address || '',
          openAt: data.opens_at.split(':').splice(0, 2).join(':'),
          closeAt: data.closes_at.split(':').splice(0, 2).join(':'),
          numbers: data.phone_numbers,
          socials: data.social_contacts,
          selectedTypes: data.types,
          location: parseLocation(data.full_location),
          country: data.country,
          showContacts: data.show_contacts,

          selectedCatID: null,
          step: 0
        }}
      >
        {(formikBag) => {
          const { values, setFieldValue, isSubmitting, handleSubmit } = formikBag;
          return (
            <form className="organization-edit-main-form" onSubmit={handleSubmit}>
              {formikBag.values.step === 0 && (
                <MainView
                  formikBag={formikBag}
                  title="Редактирование"
                  onBack={() => history.push(`/organizations/${id}`)}
                  onMap={() => setFieldValue('step', 7)}
                  onSubmit={handleSubmit}
                  submitLabel={isSubmitting ? 'Сохранение' : 'Сохранить'}
                  disabled={isSubmitting}
                >
                  <RowToggle
                    label="Развернуть контакты и web"
                    name="showContacts"
                    checked={values.showContacts}
                    onChange={formikBag.handleChange}
                    className="organization-form-main__show-contact"
                  />

                  <RowButton
                    label='Деактивировать организацию'
                    className="organization-form-main__deactivate"
                    showArrow={false}
                  >
                    <DeactivateIcon />
                  </RowButton>
                </MainView>
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
                  userGEO={userGEO}
                  position={values.location && [values.location.lat, values.location.lng]}
                />
              )}
            </form>
          )
        }}
      </Formik>
    );
  }
}

export default OrganizationEditMainForm;