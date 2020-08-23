import React from 'react';
import {InputTextField} from '../../components/UI/InputTextField';
import {FieldArray, Formik} from 'formik';
import {getRandom} from '../../common/helpers';
import {getSocials, setSocials} from '../../store/actions/profileActions';
import {connect} from 'react-redux';
import * as Yup from 'yup';
import {ERROR_MESSAGES} from '../../common/messages';
import MobileTopHeader from '../../components/MobileTopHeader';
import './index.scss';

const VALIDATION_SCHEMA = Yup.object().shape({
  socials: Yup.array().of(
    Yup.object().shape({
      id: Yup.string().required(),
      url: Yup.string().required(ERROR_MESSAGES.social_empty)
    })
  )
});

class EditSocialsPage extends React.Component {
  componentDidMount() {
    this.props.getSocials();
  }

  onSubmit = ({ socials }) => {
    this.props.setSocials(socials
      .filter(soc => soc.url)
      .map(soc => soc.url))
      .then(res => res.success && this.props.history.push('/profile/edit'));
  }

  render() {
    const { user, history } = this.props;
    const { data } = this.props.socialNetworks;
    return (
      <div className="edit-socials-page">
        <Formik
          enableReinitialize
          validationSchema={VALIDATION_SCHEMA}
          onSubmit={(values, formikBag) => this.onSubmit(values, formikBag)}
          initialValues={{
            socials: data || []
          }}
        >
          {({ values, errors, touched, setFieldValue, handleChange, handleSubmit}) => (
            <form onSubmit={handleSubmit} className="edit-socials-form">
              <MobileTopHeader
                title="Социальные сети"
                onBack={() => history.push('/profile/edit')}
                onSubmit={handleSubmit}
              />

              <div className="edit-socials-form__content">
                <div className="container">
                  <InputTextField
                    name="main"
                    label="Социальные сети"
                    value={`@apofiz/${(user && user.username.replace(' ', '')) || 'username'}`}
                    onChange={handleChange}
                    onCopy
                    disabled
                  />
                  <FieldArray
                    name="socials"
                    render={arrayHelpers => (
                      <React.Fragment>
                        {values.socials &&
                        values.socials.length > 0 &&
                        values.socials.map((soc, index) => (
                          <InputTextField
                            key={soc.id}
                            name={`socials[${index}].id`}
                            label="Социальные сети и web"
                            value={soc.url}
                            onChange={(e) => setFieldValue(`socials[${index}].url`,  e.target.value)}
                            onRemove={() => arrayHelpers.remove(index)}
                            onCopy
                            error={errors.socials && touched.socials && touched.socials[index] && errors.socials[index] && errors.socials[index].url}
                          />
                        ))}
                        <button className="edit-socials-form__add f-14" type="button" onClick={() => arrayHelpers.push({id: getRandom(400, 999), url: ''})}>
                          Добавить дополнительную ссылку
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
  user: state.userStore.user,
  socialNetworks: state.profileStore.socialNetworks
})

const mapDispatchToProps = dispatch => ({
  getSocials: () => dispatch(getSocials()),
  setSocials: socials => dispatch(setSocials(socials))
});

export default connect(mapStateToProps, mapDispatchToProps)(EditSocialsPage);