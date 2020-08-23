import React from 'react';
import {connect} from 'react-redux';
import {setUserGEO, uploadFile} from '../../store/actions/commonActions';
import OrganizationForm from '../../components/Forms/Organization/OrganizationCreateForm';
import Notify from '../../components/Notification';
import {ERROR_MESSAGES} from '../../common/messages';
import { createOrganization, getOrganizationTypes } from '../../store/actions/organizationActions';
import {getUserGEO} from '../../common/helpers';

class OrgCreatePage extends React.Component {
  componentDidMount() {
    const {getOrganizationTypes, setUserGEO} = this.props;
    getOrganizationTypes();
    getUserGEO(setUserGEO);
  }

  onSubmit = async (values, { setSubmitting }) => {
    const {
      title,
      description,
      openAt,
      closeAt,
      image,
      selectedTypes,
      numbers,
      socials,
      fixedDiscounts,
      accDiscounts,
      location,
      country,
      address
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
      numbers: numbers.map(num => num.phone_number),
      accounts: socials.map(soc => soc.url),
    };

    if (image) {
      const res = await this.props.uploadFile(image);
      const imageID = res && res.id;
      if (!imageID) {
        Notify.info({text: ERROR_MESSAGES.image_upload_fail})
        return;
      }
      payload.image_id = imageID;
    } else { return }

    const cards = [];
    fixedDiscounts.map(card => cards.push({
      type: card.type,
      percent: parseInt(card.percent),
      limit: null
    }))

    accDiscounts.map(card => cards.push({
      type: card.type,
      percent: parseInt(card.percent),
      limit: parseInt(card.limit)
    }))

    payload.cards = cards;
    const res = await this.props.createOrganization(payload);
    if (res && res.id) {
      this.props.history.push(`/organizations/${res.id}`);
    } else {
      setSubmitting(false);
    }
  }

  render() {
    const { history, orgTypes, userGEO } = this.props;

    return (
      <div className="org-create-page">
        <OrganizationForm
          orgTypes={orgTypes}
          history={history}
          userGEO={userGEO}
          onSubmit={this.onSubmit}
        />
      </div>
    );
  }
}

const mapStateToProps = state => ({
  orgTypes: state.organizationStore.orgTypes,
  userGEO: state.commonStore.userGEO,
});

const mapDispatchToProps = dispatch => ({
  uploadFile: file => dispatch(uploadFile(file)),
  getOrganizationTypes: () => dispatch(getOrganizationTypes()),
  createOrganization: payload => dispatch(createOrganization(payload)),
  setUserGEO: geo => dispatch(setUserGEO(geo)),
});

export default connect(mapStateToProps, mapDispatchToProps)(OrgCreatePage);