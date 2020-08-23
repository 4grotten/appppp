import React from 'react';
import MobileTopHeader from '../../MobileTopHeader';
import {Formik} from 'formik';
import MessageTextarea from '../../UI/TextareaMessage';
import * as Yup from 'yup';
import Button from '../../UI/Button';
import Preloader from '../../Preloader';
import RecipientsCount from '../../RecipientsCount';
import './index.scss';

const VALIDATION_SCHEMA = Yup.object({
  text: Yup.string()
    .min(1, 'Не менее одного символа')
    .max(800, 'Вы превысили лимит')
    .required('Введите сообщение')
})

const MessageForm = ({ recipients, onSubmit, onBack }) => {
  const { data, loading } = recipients;
  return (
    <Formik
      onSubmit={(values, formikBag) => onSubmit(values, formikBag)}
      validationSchema={VALIDATION_SCHEMA}
      initialValues={{
        text: ''
      }}
    >
      {({ values, errors, touched, handleChange, handleSubmit }) => (
        <form className="message-form" onSubmit={handleSubmit}>
          <MobileTopHeader
            title="Новое сообщение"
            onBack={onBack}
            submitLabel="Отправить"
            onSubmit={handleSubmit}
          />

          <div className="message-form__content">
            <div className="container">
              {loading
                ? <Preloader />
                : data && (
                <RecipientsCount
                  recipients={data.followers}
                  recipients_count={data.count}
                  className="message-form__recipients"
                />
              )}

              <MessageTextarea
                placeholder="Напишите сообщение"
                name="text"
                value={values.text}
                onChange={handleChange}
                error={errors.text && touched.text && errors.text}
                className="dddddddd"
              />

              <Button
                type="submit"
                label="Отправить"
                onSubmit={handleSubmit}
                className="message-form__submit"
              />
            </div>
          </div>
        </form>
      )}
    </Formik>
  );
};

export default MessageForm;