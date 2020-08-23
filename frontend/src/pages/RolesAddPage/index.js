import React, {Component} from 'react';
import {connect} from 'react-redux';
import {createRole} from '../../store/actions/employeeActions';
import RoleManageForm from '../../components/Forms/RoleManageForm';
import Notify from '../../components/Notification';

class RolesAddPage extends Component {
  organizationID = this.props.match.params.id;

  onSubmit = async values => {
    const res = await this.props.createRole({
      organization: this.organizationID,
      ...values
    })

    if (res && res.success) {
      Notify.success({ text: 'Новая должность успешно создана'});
      this.props.history.push(`/organizations/${this.organizationID}/roles`);
    }
  }

  render() {
    return (
      <RoleManageForm
        onBack={() => this.props.history.push(`/organizations/${this.organizationID}/roles`)}
        onSubmit={this.onSubmit}
      />
    );
  }
}

const mapDispatchToProps = dispatch => ({
  createRole: payload => dispatch(createRole(payload)),
})

export default connect(null, mapDispatchToProps)(RolesAddPage);