import React from 'react';
import OrganizationModule from '../../containers/OrganizationModule';
import {getCardBackgrounds, getOrganizationDetail} from '../../store/actions/organizationActions';
import {connect} from 'react-redux';
import MapView from '../../containers/MapView';
import {copyTextToClipboard} from '../../common/utils';

class OrganizationDetailPage extends React.Component {
  componentDidMount() {
    const { id } = this.props.match.params;
    const { user } = this.props;
    this.props.getOrganizationDetail(id);
    user && this.props.getCardBackgrounds();
  }

  state = {
    step: 0
  }

  setStep = step => this.setState({ step });

  render() {
    const { orgDetail, history } = this.props;
    const position = orgDetail.data && [orgDetail.data.full_location.latitude, orgDetail.data.full_location.longitude];

   return (
     <div className="organization-detail-page">
       {this.state.step === 0 && (
         <OrganizationModule
           id={this.props.match.params.id}
           onAddressClick={() => this.setStep(1)}
           history={history}
         />
       )}

       {this.state.step === 1 && (
         <MapView
           onBack={() => this.setStep(0)}
           position={position}
           buttonLabel="Скопировать"
           onClick={() => position && copyTextToClipboard(JSON.stringify(position))}
         />
       )}
     </div>
   )
  }
}

const mapStateToProps = state => ({
  user: state.userStore.user,
  orgDetail: state.organizationStore.orgDetail
})

const mapDispatchToProps = dispatch => ({
  getOrganizationDetail: id => dispatch(getOrganizationDetail(id)),
  getCardBackgrounds: () => dispatch(getCardBackgrounds())
})

export default connect(mapStateToProps, mapDispatchToProps)(OrganizationDetailPage);