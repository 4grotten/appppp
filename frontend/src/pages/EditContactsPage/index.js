import React from 'react';
import {InputTextField} from '../../components/UI/InputTextField';
import {FieldArray, Formik} from 'formik';
import {getRandom, PHONE_NUMBER} from '../../common/helpers';
import {getPhoneNumbers, setPhoneNumbers} from '../../store/actions/profileActions';
import {connect} from 'react-redux';
import * as Yup from 'yup';
import {ERROR_MESSAGES} from '../../common/messages';
import MobileTopHeader from '../../components/MobileTopHeader';
import './index.scss';

const VALIDATION_SCHEMA = Yup.object().shape({
  numbers: Yup.array().of(
    Yup.object().shape({
      id: Yup.string().required(),
      phone_number: Yup.string().min(4, ERROR_MESSAGES.phone_empty).required(ERROR_MESSAGES.phone_empty)
    })
  )
});

class EditContactsPage extends React.Component {
  componentDidMount() {
    this.props.getPhoneNumbers();
  }

  onSubmit = ({ numbers }) => {
    this.props.setPhoneNumbers(numbers
      .filter(num => num.phone_number)
      .map(num => num.phone_number))
      .then(res => res.success && this.props.history.push('/profile/edit'));
  }

  render() {
    const { user, history } = this.props;
    const { data } = this.props.phoneNumbers;
    return (
      <div className="edit-contacts-page">
        <Formik
          enableReinitialize
          validationSchema={VALIDATION_SCHEMA}
          onSubmit={(values, formikBag) => this.onSubmit(values, formikBag)}
          initialValues={{
            numbers: data || []
          }}
        >
          {({ values, errors, touched, setFieldValue, handleChange, handleSubmit}) => (
            <form onSubmit={handleSubmit} className="edit-contacts-form">
              <MobileTopHeader
                onBack={() => history.push('/profile/edit')}
                onSubmit={handleSubmit}
                title="Номер телефона"
              />
              <div className="edit-contacts-form__content">
                <div className="container">
                  <InputTextField
                    name="main"
                    label="Номер авторизации"
                    value={(user && user.phone_number) || ''}
                    onChange={handleChange}
                    onCopy
                    disabled
                  />
                  <FieldArray
                    name="numbers"
                    render={arrayHelpers => (
                      <React.Fragment>
                        {values.numbers &&
                        values.numbers.length > 0 &&
                        values.numbers.map((num, index) => (
                          <InputTextField
                            key={num.id}
                            name={`numbers[${index}].id`}
                            label="Контактный номер"
                            value={num.phone_number}
                            onChange={(e) => e.target.value.match(PHONE_NUMBER) && setFieldValue(`numbers[${index}].phone_number`,  e.target.value)}
                            onRemove={() => arrayHelpers.remove(index)}
                            onCopy
                            error={errors.numbers && touched.numbers && touched.numbers[index] && errors.numbers[index] && errors.numbers[index].phone_number}
                          />
                        ))}
                        <button className="edit-contacts-form__add f-14" type="button" onClick={() => arrayHelpers.push({id: getRandom(400, 999), phone_number: ''})}>
                          Добавить дополнительный номер
                        </button>
                      </React.Fragment>
                    )}
                  />
                </div>
              </div>
            </form>
          )}
        </Formik>
      </div>
    )
  }
}

const mapStateToProps = state => ({
  phoneNumbers: state.profileStore.phoneNumbers
})

const mapDispatchToProps = dispatch => ({
  getPhoneNumbers: () => dispatch(getPhoneNumbers()),
  setPhoneNumbers: phones => dispatch(setPhoneNumbers(phones))
});

export default connect(mapStateToProps, mapDispatchToProps)(EditContactsPage);