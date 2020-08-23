import React, {Component} from 'react';
import {connect} from 'react-redux';
import {getRoleDetail, removeRole, updateRole} from '../../store/actions/employeeActions';
import RoleManageForm from '../../components/Forms/RoleManageForm';
import Preloader from '../../components/Preloader';

class RolesEditPage extends Component {
  organizationID = this.props.match.params.id;
  roleID = this.props.match.params.roleID;

  componentDidMount() {
    this.props.getRoleDetail(this.roleID)
  }

  onSubmit = async (values, { setSubmitting }) => {
    const res = await this.props.updateRole(this.roleID, values);
    if (res && res.success) {
      return this.props.history.push(`/organizations/${this.organizationID}/roles`);
    }

    setSubmitting(false);
  }

  onRemove = async () => {
    const res = await this.props.removeRole(this.roleID);
    if (res && res.success) {
      this.props.history.push(`/organizations/${this.organizationID}/roles`);
    }
  }

  render() {
    const { data, loading } = this.props.roleDetail;
    return loading ? <Preloader style={{ height: '80vh'}} /> : (
      <RoleManageForm
        data={data}
        onSubmit={this.onSubmit}
        onBack={() => this.props.history.push(`/organizations/${this.organizationID}/roles`)}
        onRemove={this.onRemove}
      />
    );
  }
}

const mapStateToProps = state => ({
  roleDetail: state.employeeStore.roleDetail,
})

const mapDispatchToProps = dispatch => ({
  getRoleDetail: roleID => dispatch(getRoleDetail(roleID)),
  updateRole: (roleID, data) => dispatch(updateRole(roleID, data)),
  removeRole: roleID => dispatch(removeRole(roleID)),
})

export default connect(mapStateToProps, mapDispatchToProps)(RolesEditPage);