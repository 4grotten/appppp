import React from 'react';
import {connect} from 'react-redux';
import {setUserGEO, uploadFile} from '../../store/actions/commonActions';
import Notify from '../../components/Notification';
import OrganizationEditMainForm from '../../components/Forms/Organization/OrganizationEditMainForm';
import {getUserGEO} from '../../common/helpers';
import {
  editOrganization,
  getOrganizationTypes,
  setOrganizationPhones, setOrganizationSocials
} from '../../store/actions/organizationActions';

class OrgEditMainPage extends React.Component {
  componentDidMount() {
    const organization = this.props.orgDetail.data;
    const { id } = this.props.match.params;
    const { getOrganizationTypes, setUserGEO, history } = this.props;

    if (!organization) {
      return history.push(`/organizations/${id}`);
    }

    getOrganizationTypes();
    getUserGEO(setUserGEO);
  }

  onSubmit = async (values, { setSubmitting }) => {
    const { id } = this.props.match.params;
    const { data } = this.props.orgDetail;
    const {
      title,
      description,
      openAt,
      closeAt,
      image,
      selectedTypes,
      numbers,
      socials,
      location,
      country,
      address,
      showContacts
    } = values;

    const payload = {
      title,
      description,
      opens_at: openAt,
      closes_at: closeAt,
      address,
      longitude: location && location.lng || null,
      latitude: location && location.lat || null,
      currency: country && country.currency.code,
      country: country && country.code,
      types: selectedTypes.map(type => type.id),
      show_contacts: showContacts,
      image_id: data && data.image && data.image.id
    };

    if (image) {
      const res = await this.props.uploadFile(image);
      const imageID = res && res.id;
      if (!imageID) {
        Notify.info({text: 'Не удалось загрузить изображение'})
        return;
      }
      payload.image_id = imageID;
    }

    this.props.setOrganizationPhones({
      phone_numbers: numbers.map(num => num.phone_number)
    }, id);

    this.props.setOrganizationSocials({
      networks: socials.map(soc => soc.url)
    }, id);

    const res = await this.props.editOrganization(id, payload);
    if (res && res.error) {
     setSubmitting(false);
    }
  }

  render() {
    const { history, orgTypes, orgDetail, userGEO, match } = this.props;
    const { data } = orgDetail;

    if (!data) {
      return null;
    }

    return (
      <div className="organization-edit-main-page">
        <OrganizationEditMainForm
          orgTypes={orgTypes}
          id={match.params.id}
          data={data}
          history={history}
          userGEO={userGEO}
          onSubmit={this.onSubmit}
        />
      </div>
    );
  }
}

const mapStateToProps = state => ({
  orgDetail: state.organizationStore.orgDetail,
  orgTypes: state.organizationStore.orgTypes,
  userGEO: state.commonStore.userGEO,
});

const mapDispatchToProps = dispatch => ({
  uploadFile: file => dispatch(uploadFile(file)),
  getOrganizationTypes: () => dispatch(getOrganizationTypes()),
  editOrganization: (id, payload) => dispatch(editOrganization(id, payload)),
  setOrganizationPhones: (phones, id) => dispatch(setOrganizationPhones(phones, id)),
  setOrganizationSocials: (socials, id) => dispatch(setOrganizationSocials(socials, id)),
  setUserGEO: geo => dispatch(setUserGEO(geo)),
});

export default connect(mapStateToProps, mapDispatchToProps)(OrgEditMainPage);
