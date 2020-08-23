import React from 'react';
import MobileTopHeader from '../../MobileTopHeader';
import {FieldArray} from 'formik';
import {InputTextField} from '../../UI/InputTextField';
import {getRandom, PHONE_NUMBER} from '../../../common/helpers';

const ContactsView = ({ formikBag, onBack, onSave }) => {
  const { values, setFieldValue } = formikBag;
  return (
    <div className="organization-form-contacts">
      <MobileTopHeader
        title="Номер телефона"
        onBack={onBack}
        onNext={onSave}
        nextLabel="Сохранить"
      />
      <div className="container">
        <FieldArray
          name="numbers"
          render={arrayHelpers => {
            return (
              <React.Fragment>
                {values.numbers.map((num, index) => (
                  <InputTextField
                    key={num.id}
                    name={`numbers[${index}].id`}
                    label="Контактный номер"
                    value={num.phone_number}
                    onChange={(e) => e.target.value.match(PHONE_NUMBER) && setFieldValue(`numbers[${index}].phone_number`, e.target.value)}
                    onRemove={() => arrayHelpers.remove(index)}
                    onCopy
                  />
                ))}
                <button className="organization-form-contacts__add f-14" type="button" onClick={() => arrayHelpers.push({id: getRandom(400, 999), phone_number: ''})}>
                  Добавить дополнительный номер
                </button>
              </React.Fragment>
            )
          }}
        />
      </div>
    </div>
  );
};

export default ContactsView;