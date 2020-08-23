import React from 'react';
import {Formik} from 'formik';
import MobileTopHeader from '../../MobileTopHeader';
import Avatar from '../../UI/Avatar';
import RolesView from '../../../containers/RolesView';
import {ArrowRight} from '../../UI/Icons';
import * as Yup from 'yup';
import Button from '../../UI/Button';
import RoleManageForm from '../RoleManageForm';
import Notify from '../../Notification';
import './index.scss';

const VALIDATION_SCHEMA = Yup.object().shape({
  role: Yup.object().shape({
    id: Yup.string().required(),
    title: Yup.string().required(),
  }).required()
})

const EmployeeManageForm = props => {
  const { invite, title, onBack, onSubmit, onRoleSelect, onTransferOwnership, createRole, organizationID, children } = props;
  return (
    <Formik
      onSubmit={(values, formikBag) => onSubmit(values, formikBag)}
      validationSchema={VALIDATION_SCHEMA}
      initialValues={{
        step: 0,
        role: (invite && invite.role) || null,
      }}
    >
      {formikBag => {
        const { values, setValues, setFieldValue, handleSubmit } = formikBag;

        return (
          <React.Fragment>
            {values.step === 0 && (
              <form onSubmit={handleSubmit}>
                <MobileTopHeader
                  onBack={onBack}
                  title={title || "Новый сотрудник"}
                  onSubmit={onSubmit && handleSubmit}
                  submitLabel="Добавить"
                />

                <div className="container">
                  <div className="employee-manage-form__user">
                    <Avatar
                      src={invite && invite.avatar && invite.avatar.medium}
                      alt={invite && invite.full_name}
                      size={50}
                      className="employee-manage-form__user-avatar"
                    />
                    <p className="f-17 tl">{(invite && invite.full_name) || ''}</p>
                  </div>

                  <div className="employee-manage-form__phone">
                    <p className="f-14">Телефон</p>
                    <p className="f-17 f-500">{(invite && invite.phone_number) || ''}</p>
                  </div>

                  <div className="employee-manage-form__role" onClick={() => setFieldValue('step', 1)}>
                    {values.role && <label className="f-14" htmlFor="role">Выбор должности</label>}
                    <input
                      value={values.role && values.role.title || ''}
                      className="f-17 f-500"
                      name="role"
                      id="role"
                      placeholder="Выбор должности"
                      readOnly
                    />
                    <ArrowRight />
                  </div>

                  {children}

                  {onTransferOwnership && (
                    <Button
                      type="button"
                      onClick={onTransferOwnership}
                      label="Назначить собственника"
                      className="employee-manage-form__btn-owner"
                    />
                  )}
                </div>
              </form>
            )}

            {values.step === 1 && (
              <RolesView
                selection={values.role && values.role.id}
                onBack={() => setFieldValue('step', 0)}
                onSelect={role => onRoleSelect ? onRoleSelect(role, formikBag) : setValues({ role: role, step: 0})}
                onAddRole={createRole ? () => setFieldValue('step', 2) : null}
                organizationID={organizationID}
              />
            )}

            {values.step === 2 && createRole && (
              <RoleManageForm
                onBack={() => setFieldValue('step', 1)}
                onSubmit={async roleValues => {
                  const res = await createRole({
                    organization: organizationID,
                    ...roleValues
                  });

                  if (res && res.success) {
                    Notify.success({ text: 'Новая должность успешно создана'});
                    setFieldValue('step', 1);
                  }}}
              />
            )}
          </React.Fragment>
        )
      }}
    </Formik>
  );
};

export default EmployeeManageForm;