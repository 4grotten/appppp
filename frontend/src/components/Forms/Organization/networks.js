import React from 'react';
import MobileTopHeader from '../../MobileTopHeader';
import {FieldArray} from 'formik';
import {InputTextField} from '../../UI/InputTextField';
import {getRandom} from '../../../common/helpers';
import './index.scss';

const NetworksView = ({ formikBag, onBack, onSave }) => {
  const { values, setFieldValue } = formikBag;
  return (
    <div className="organization-form-networks">
      <MobileTopHeader
        title="Социальные сети"
        onBack={onBack}
        onNext={onSave}
        nextLabel="Сохранить"
      />
      <div className="container">
        <FieldArray
          name="socials"
          render={arrayHelpers => {
            return (
              <React.Fragment>
                {values.socials.map((soc, index) => (
                  <InputTextField
                    key={soc.id}
                    name={`socials[${index}].id`}
                    label="Социальные сети и web"
                    value={soc.url}
                    onChange={(e) => setFieldValue(`socials[${index}].url`,  e.target.value)}
                    onRemove={() => arrayHelpers.remove(index)}
                    onCopy
                  />
                ))}
                <button className="organization-form-networks__add f-14" type="button" onClick={() => arrayHelpers.push({id: getRandom(400, 999), url: ''})}>
                  Добавить дополнительную ссылку
                </button>
              </React.Fragment>
            )
          }}
        />
      </div>
    </div>
  );
};

export default NetworksView;