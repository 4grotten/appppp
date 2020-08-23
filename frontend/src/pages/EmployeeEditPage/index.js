import React, {Component} from 'react';
import EmployeeManageForm from '../../components/Forms/EmployeeManageForm';
import {connect} from 'react-redux';
import {getOrganizationDetail} from '../../store/actions/organizationActions';
import Preloader from '../../components/Preloader';
import RowLink from '../../components/UI/RowLink';
import {ExitIcon, InsightIcon} from '../../components/UI/Icons';
import RowButton from '../../components/UI/RowButton';
import {
  createRole,
  getEmployeeDetail, removeEmployee,
  setOrganizationOwner,
  updateEmployeeRole
} from '../../store/actions/employeeActions';
import './index.scss';

class EmployeeEditPage extends Component {
  organizationID = this.props.match.params.id;
  employeeID = this.props.match.params.employeeID;

  componentDidMount() {
    this.props.getEmployeeDetail(this.employeeID, () => this.props.history.push(`/organizations/${this.organizationID}/employees`));
    this.props.getOrganizationDetail(this.organizationID);
  }

  onRoleSelect = (role, formikBag) => {
    const allow = window.confirm('Вы действительно хотите сменить должность ?');
    if (allow) {
      this.props.updateEmployeeRole(this.employeeID, role.id).then(res => {
        (res && res.success)
          ? formikBag.setValues({ role: role, step: 0})
          : formikBag.setFieldValue('step', 0);
      })
    } else {
      return formikBag.setFieldValue('step', 0);
    }
  }

  onTransferOwnership = () => {
    const { selectedEmployee, setOrganizationOwner, history } = this.props;
    if (selectedEmployee) {
      const allow = window.confirm('Вы действительно хотите передать права собственника ?');
      allow && setOrganizationOwner(this.organizationID, selectedEmployee.userID).then(res => {
        res && res.success && history.push(`/organizations/${this.organizationID}`);
      });
    }
  }

  render() {
    const { employeeDetail, orgDetail, createRole, removeEmployee, history } = this.props;
    const { data, loading } = employeeDetail;
    const isOwner = orgDetail.data && orgDetail.data.permissions && orgDetail.data.permissions.is_owner;

    return (
      <div className="employee-edit-page">
        {loading ? <Preloader className="employee-edit-page__preloader" /> : data && (
          <EmployeeManageForm
            title="Настройки работника"
            invite={{
              ...data.user,
              id: data.id,
              userID: data.user.id,
              role: data.role,
            }}
            organizationID={this.organizationID}
            onBack={() => history.push(`/organizations/${this.organizationID}/employees`)}
            onRoleSelect={this.onRoleSelect}
            createRole={createRole}
            onTransferOwnership={isOwner && this.onTransferOwnership}
          >
            <React.Fragment>
              <RowLink
                to={`/organizations/${this.organizationID}/employees/${this.employeeID}/attendance`}
                label="Статистика посещений"
                className="employee-edit-page__stats"
              >
                <InsightIcon />
              </RowLink>
              <RowButton
                label="Уволить сотрудника"
                showArrow={false}
                onClick={() => removeEmployee(this.employeeID).then(res => res && res.success && history.push(`/organizations/${this.organizationID}/employees`))}
                className="employee-edit-page__fire-employee"
              >
                <ExitIcon />
              </RowButton>
            </React.Fragment>
          </EmployeeManageForm>
        )}
      </div>
    );
  }
}

const mapStateToProps = state => ({
  orgDetail: state.organizationStore.orgDetail,
  employeeDetail: state.employeeStore.employeeDetail,
})

const mapDispatchToProps = dispatch => ({
  updateEmployeeRole: (employeeID, roleID) => dispatch(updateEmployeeRole(employeeID, roleID)),
  setOrganizationOwner: (orgID, userID) => dispatch(setOrganizationOwner(orgID, userID)),
  getOrganizationDetail: orgID => dispatch(getOrganizationDetail(orgID)),
  getEmployeeDetail: (employeeID, redirect) => dispatch(getEmployeeDetail(employeeID, redirect)),
  createRole: payload => dispatch(createRole(payload)),
  removeEmployee: id => dispatch(removeEmployee(id)),
})

export default connect(mapStateToProps, mapDispatchToProps)(EmployeeEditPage);