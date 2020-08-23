import * as React from 'react';
import * as classnames from 'classnames';
import {Formik} from 'formik';
import {InputTextField} from '../../UI/InputTextField';
import GenderSelect from '../../UI/GenderSelect';
import {PasswordField} from '../../UI/PasswordField';
import Button from '../../UI/Button';
import {ALLOWED_FORMATS, GENDER} from '../../../common/constants';
import DatePickerCalendar from '../../UI/DatePickerCalendar';
import AvatarEdit, {cropAvatar} from '../../UI/AvatarEdit';
import Avatar from '../../UI/Avatar';
import * as Yup from 'yup';
import {ERROR_MESSAGES} from '../../../common/messages';
import MobileTopHeader from '../../MobileTopHeader';
import {checkForValidFile} from '../../../common/helpers';
import './index.scss';

const VALIDATION_SCHEMA = Yup.object().shape({
  avatar: Yup.mixed().required(),
  nickname: Yup.string().required(ERROR_MESSAGES.username_empty),
  fullname: Yup.string().required(ERROR_MESSAGES.fullname),
  email: Yup.string()
    .required(ERROR_MESSAGES.email_empty)
    .email(ERROR_MESSAGES.email_format),
  gender: Yup.string().required(ERROR_MESSAGES.gender_empty),
  birthday: Yup.date().required(ERROR_MESSAGES.birthday_empty),
  password: Yup.string().min(6, ERROR_MESSAGES.password_min).required(ERROR_MESSAGES.password_empty)
});

class ProfileForm extends React.Component {
  preSubmit = (values, formikBag) => {
    if (values.editorRef) {
      const croppedAvatar = cropAvatar(values.editorRef);
      this.props.onSubmit({...values, croppedAvatar}, formikBag);
    }
  }

  render() {
    const { setStep } = this.props;

    return (
      <Formik
        validationSchema={VALIDATION_SCHEMA}
        onSubmit={(values, formikBag) => this.preSubmit(values, formikBag)}
        initialValues={{
          gender: GENDER.male,
          avatar: null,
          croppedAvatar: null,
          editorRef: null,
          nickname: '',
          email: '',
          password: '',
          fullname: '',
          birthday: new Date()
        }}
      >
        {({values, handleChange, handleSubmit, setFieldValue, errors, touched, isSubmitting}) => (
          <form className="profile-form" onSubmit={handleSubmit}>
            <MobileTopHeader
              title="Профиль"
              onBack={() => setStep(0)}
              onSubmit={handleSubmit}
              submitLabel={isSubmitting ? 'Сохранение' : 'Сохранить'}
              disabled={isSubmitting}
            />

            <div className="container">
              <div  className="profile-form__avatar">
                {values.avatar
                  ? (
                    <AvatarEdit
                      src={values.avatar}
                      setFieldValue={setFieldValue}
                      error={errors.avatar && touched.avatar && errors.avatar}
                    />
                  ) : (
                    <Avatar
                      src={values.avatarUrl}
                      alt={values.gender}
                      gender={values.gender}
                      className="profile-form__avatar-icon"
                      error={errors.avatar && touched.avatar && errors.avatar}
                    />
                  )}
              </div>

              <div className="profile-form__avatar-control">
                <label
                  htmlFor="avatar"
                  className={classnames("profile-form__avatar-label", errors.avatar && touched.avatar && errors.avatar && "profile-form__avatar-label-error")}
                >
                  Добавить фото профиля
                </label>
                <input
                  type="file"
                  name="avatar"
                  id="avatar"
                  className="profile-form__avatar-input"
                  onChange={e => {
                    const file = e.target.files[0];
                    console.log('original', file);
                    const { isValid } = checkForValidFile(file, ALLOWED_FORMATS);
                    isValid && setFieldValue('avatar', file);
                  }}
                />
              </div>

              <GenderSelect
                onChange={gender => setFieldValue('gender', gender)}
                value={values.gender}
                className="profile-form__gender"
              />

              <InputTextField
                label="ФИО"
                name="fullname"
                value={values.fullname}
                onChange={handleChange}
                className="profile-form__fullname"
                error={errors.fullname && touched.fullname && errors.fullname}
              />
              <InputTextField
                label="Никнейм"
                name="nickname"
                value={values.nickname}
                onChange={handleChange}
                className="profile-form__nickname"
                error={errors.nickname && touched.nickname && errors.nickname}
              />
              <InputTextField
                label="Email"
                name="email"
                value={values.email}
                onChange={handleChange}
                className="profile-form__email"
                error={errors.email && touched.email && errors.email}
              />
              <DatePickerCalendar
                label="Дата рождения"
                onChange={date => setFieldValue('birthday', date)}
                value={values.birthday}
                className="profile-form__birthday"
              />
              <PasswordField
                label="Пароль"
                value={values.password}
                onChange={handleChange}
                onClear={() => setFieldValue('password', '')}
                error={errors.password && touched.password && errors.password}
                className="profile-form__password"
              />
              <Button
                label="Сохранить"
                className="profile-form__submit"
                type="submit"
                onSubmit={handleSubmit}
                disabled={isSubmitting}
              />
            </div>
          </form>
        )}
      </Formik>
    )
  }
}

export default ProfileForm;