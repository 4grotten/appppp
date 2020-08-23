import React from 'react';
import {Formik} from 'formik';
import {InputTextField} from '../../UI/InputTextField';
import MobileTopHeader from '../../MobileTopHeader';
import RowToggle from '../../UI/RowToggle';
import Button from '../../UI/Button';
import * as Yup from 'yup';
import './index.scss';

const VALIDATION_SCHEMA = Yup.object().shape({
  title: Yup.string().required('Введите должность')
})

const RoleManageForm = ({ onSubmit, data, onBack, onRemove }) => (
  <Formik
    enableReinitialize
    validationSchema={VALIDATION_SCHEMA}
    onSubmit={(values, formikBag) => onSubmit(values, formikBag)}
    initialValues={{
      title: (data && data.title) || '',
      can_sale: !!(data && data.can_sale),
      can_check_attendance: !!(data && data.can_check_attendance),
      can_see_stats: !!(data && data.can_see_stats),
      can_edit_organization: !!(data && data.can_edit_organization),
      can_send_message: !!(data && data.can_send_message),
      can_edit_partner: !!(data && data.can_edit_partner),
    }}
  >
    {({ values, errors, touched, handleChange, handleSubmit, isSubmitting }) => (
      <form
        onSubmit={handleSubmit}
        className="role-manage-form"
      >
        <MobileTopHeader
          title={data ? data.title : "Новая должность" }
          onBack={onBack}
          onSubmit={handleSubmit}
        />

        <div className="container">
          <div className="role-manage-form__content">
            <div>
              <InputTextField
                name="title"
                label="Название должности"
                value={values.title}
                onChange={handleChange}
                error={errors.title && touched.title && errors.title}
              />

              <h2 className="role-manage-form__manage f-14 f-600">Управление</h2>
              <RowToggle
                name="can_check_attendance"
                label="Сканировать пропуска"
                checked={values.can_check_attendance}
                onChange={handleChange}
              />
              <RowToggle
                name="can_see_stats"
                label="Статистика продаж/скидок"
                checked={values.can_see_stats}
                onChange={handleChange}
              />
              <RowToggle
                name="can_edit_organization"
                label="Редактировать организацию"
                checked={values.can_edit_organization}
                onChange={handleChange}
              />
              <RowToggle
                name="can_sale"
                label="Проводить скидки"
                checked={values.can_sale}
                onChange={handleChange}
              />
              <RowToggle
                name="can_send_message"
                label="Отправлять сообщения"
                checked={values.can_send_message}
                onChange={handleChange}
              />
              <RowToggle
                name="can_edit_partner"
                label="Функции партнеров"
                checked={values.can_edit_partner}
                onChange={handleChange}
              />
            </div>

            {onRemove && (
              <Button
                type="button"
                label="Удалить"
                className="role-manage-form__remove"
                disabled={isSubmitting}
                onClick={onRemove}
              />
            )}
          </div>
        </div>
      </form>
    )}
  </Formik>
);

export default RoleManageForm;