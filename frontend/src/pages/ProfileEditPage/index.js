import React, {Component} from 'react';
import * as moment from 'moment';
import {Formik} from 'formik';
import {ALLOWED_FORMATS, DATE_FORMAT_YYYY_MM_DD, GENDER} from '../../common/constants';
import {connect} from 'react-redux';
import {getUser, logoutUser} from '../../store/actions/userActions';
import AvatarEdit, {cropAvatar} from '../../components/UI/AvatarEdit';
import Avatar from '../../components/UI/Avatar';
import GenderSelect from '../../components/UI/GenderSelect';
import {InputTextField} from '../../components/UI/InputTextField';
import DatePickerCalendar from '../../components/UI/DatePickerCalendar';
import {ContactIcon, ExitIcon, PassIcon, PhoneIcon, WebIcon} from '../../components/UI/Icons';
import RowLink from '../../components/UI/RowLink';
import {updateProfile} from '../../store/actions/profileActions';
import {setAuthChangeCode, uploadFile} from '../../store/actions/commonActions';
import {ERROR_MESSAGES} from '../../common/messages';
import * as Yup from 'yup';
import Notify from '../../components/Notification';
import MobileTopHeader from '../../components/MobileTopHeader';
import RowButton from '../../components/UI/RowButton';
import {getRandom} from '../../common/helpers';
import './index.scss';

const VALIDATION_SCHEMA = Yup.object().shape({
  nickname: Yup.string().required(ERROR_MESSAGES.username_empty),
  fullname: Yup.string().required(ERROR_MESSAGES.fullname),
  email: Yup.string()
    .required(ERROR_MESSAGES.email_empty)
    .email(ERROR_MESSAGES.email_format)
});

class ProfileEditPage extends Component {
  componentDidMount() {
    this.props.getUser();
  }

  onSubmit = async data => {
    const { user } = this.props;

    try {
      const payload = {
        gender: data.gender,
        username: data.nickname,
        email: data.email,
        full_name: data.fullname,
        date_of_birth: moment(data.birthday).format(DATE_FORMAT_YYYY_MM_DD)
      };

      if (data.avatar && data.editorRef) {
        const croppedAvatar = cropAvatar(data.editorRef);
        const res = await this.props.uploadFile(croppedAvatar);
        res && res.id && (payload.avatar_id = res.id);
      } else {
        payload.avatar_id = user && user.avatar && user.avatar.id;
      }

      if (!payload.avatar_id) {
        return Notify.info({ text: 'Could not upload image' })
      }

      this.props.updateProfile(payload).then(
        res => res && res.success && this.props.history.push('/profile')
      );
    } catch (e) {}
  }

  render() {
    const { user, history } = this.props;

    return (
      <div className="profile-edit-page">
        <Formik
          validationSchema={VALIDATION_SCHEMA}
          onSubmit={(values, formikBag) => this.onSubmit(values, formikBag)}
          initialValues={{
            gender: user.gender || GENDER.male,
            avatar: null,
            croppedAvatar: null,
            editorRef: null,
            nickname: user.username || '',
            email: user.email || '',
            fullname: user.full_name || '',
            birthday: user.date_of_birth && moment(user.date_of_birth).toDate() || new Date()
          }}
        >
          {({values, errors, touched, handleChange, setFieldValue, handleSubmit}) => (
            <form onSubmit={handleSubmit} className="profile-edit-page__form">
              <MobileTopHeader
                title="Редактирование"
                onBack={() => history.push('/profile')}
                onSubmit={handleSubmit}
              />

              <div className="container">
                <div  className="profile-edit-page__avatar">
                  {values.avatar
                    ? (
                      <AvatarEdit
                        src={values.avatar}
                        setFieldValue={setFieldValue}
                        error={errors.avatar && touched.avatar && errors.avatar}
                      />
                    ) : (
                      <Avatar
                        src={user.avatar && user.avatar.large}
                        alt={values.fullname}
                        gender={values.gender}
                        className="profile-edit-page__avatar-icon"
                      />
                    )}
                </div>
                <div className="profile-form__avatar-control">
                  <label
                    htmlFor="avatar"
                    className="profile-form__avatar-label"
                  >
                    {(user.avatar && user.avatar.file || values.avatar) ? 'Сменить фото профиля' : 'Добавить фото профиля'}
                  </label>
                  <input
                    type="file"
                    name="avatar"
                    id="avatar"
                    className="profile-form__avatar-input"
                    onChange={e => {
                      const { type } = e.target.files[0];
                      if (ALLOWED_FORMATS.includes(type)) {
                        setFieldValue([e.target.name], e.target.files[0]);
                      }
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

                <DatePickerCalendar
                  label="Дата рождения"
                  onChange={date => setFieldValue('birthday', date)}
                  value={values.birthday}
                  className="profile-form__birthday"
                  error={errors.birthday && touched.birthday && errors.birthday}
                />

                <InputTextField
                  label="Email"
                  name="email"
                  value={values.email}
                  onChange={handleChange}
                  className="profile-form__email"
                  error={errors.email && touched.email && errors.email}
                />
              </div>
            </form>
          )}
        </Formik>

        <div className="container">
          <div className="profile-edit-page__links">
            <RowLink label="Контакты" to="edit-contacts" >
              <ContactIcon />
            </RowLink>

            <RowLink label="Web / Социальные сети" to="edit-socials" >
              <WebIcon />
            </RowLink>

            <RowLink label="Сменить пароль" to="edit-password" >
              <PassIcon />
            </RowLink>

            <RowButton label="Сменить номер авторизации" to="edit-phone" onClick={async () => {
              const confim = confirm("Вы действительно желаете сменить номер авторизации ?");
              if (confim) {
                const randomCode = JSON.stringify(getRandom(0, 245));
                await this.props.setAuthChangeCode(randomCode);
                this.props.history.push(`/profile/edit-auth/${randomCode}`)
              }
            }} >
              <PhoneIcon />
            </RowButton>

            <RowButton
              label="Выйти"
              showArrow={false}
              onClick={async () => {
                const allowed = confirm("Вы действительно желаете выйти ?");
                allowed && this.props.logout()
              }}
            >
              <ExitIcon />
            </RowButton>
          </div>
        </div>
      </div>
    );
  }
}

const mapStateToProps = state => ({
  user: state.userStore.user,
})

const mapDispatchToProps = dispatch => ({
  updateProfile: data => dispatch(updateProfile(data)),
  uploadFile: file => dispatch(uploadFile(file)),
  setAuthChangeCode: code => dispatch(setAuthChangeCode(code)),
  getUser: () => dispatch(getUser()),
  logout: () => dispatch(logoutUser())
})

export default connect(mapStateToProps, mapDispatchToProps)(ProfileEditPage);