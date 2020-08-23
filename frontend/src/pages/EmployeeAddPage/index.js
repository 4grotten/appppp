import React from 'react';
import {connect} from 'react-redux';
import EmployeeManageForm from '../../components/Forms/EmployeeManageForm';
import {addEmployee, createRole, setOrganizationOwner} from '../../store/actions/employeeActions';
import {getOrganizationDetail} from '../../store/actions/organizationActions';

class EmployeeAddPage extends React.Component {
  organizationID = this.props.match.params.id;

  componentDidMount() {
    if (!this.props.invite) {
      this.props.history.push(`/organizations/${this.organizationID}/employees`)
    }
    this.props.getOrganizationDetail(this.organizationID);
  }

  onSubmit = async ({ role }) => {
    const { invite } = this.props;
    const payload = {
      role: role.id,
      user: invite && invite.id,
      organization: this.organizationID,
    }
    const res = await this.props.addEmployee(payload);
    if (res && res.success) {
     this.props.history.push(`/organizations/${this.organizationID}/employees`);
    }
  }

  onTransferOwnership = () => {
    const { invite, setOrganizationOwner, history } = this.props;
    if (invite) {
      const allow = window.confirm('Вы действительно хотите передать права собственника ?');
      allow && setOrganizationOwner(this.organizationID, invite.id).then(res => {
        res && res.success && history.push(`/organizations/${this.organizationID}`);
      });
    }
  }

  render() {
    const { orgDetail, createRole } = this.props;
    const isOwner = orgDetail.data && orgDetail.data.permissions && orgDetail.data.permissions.is_owner;
    return (
      <EmployeeManageForm
        invite={this.props.invite}
        onBack={() => this.props.history.push(`/organizations/${this.organizationID}/employees`)}
        onSubmit={this.onSubmit}
        organizationID={this.organizationID}
        createRole={createRole}
        onTransferOwnership={isOwner && this.onTransferOwnership}
      />
    );
  }
}

const mapStateToProps = state => ({
  invite: state.employeeStore.invite,
  orgDetail: state.organizationStore.orgDetail,
})

const mapDispatchToProps = dispatch => ({
  addEmployee: data => dispatch(addEmployee(data)),
  setOrganizationOwner: (orgID, userID) => dispatch(setOrganizationOwner(orgID, userID)),
  getOrganizationDetail: orgID => dispatch(getOrganizationDetail(orgID)),
  createRole: payload => dispatch(createRole(payload)),
})

export default connect(mapStateToProps, mapDispatchToProps)(EmployeeAddPage);