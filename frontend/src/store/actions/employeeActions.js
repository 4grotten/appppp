import axios from '../../axios-api';
import Pathes from '../../common/pathes';
import {getMessage} from '../../common/helpers';
import {
  GET_EMPLOYEE_DETAIL,
  GET_EMPLOYEE_INFO,
  GET_EMPLOYEES,
  GET_ROLE_DETAIL,
  GET_ROLES
} from '../actionTypes/employeeTypes';
import {getQuery} from '../../common/utils';
import Notify from '../../components/Notification';

const getEmployeesRequest = () => ({ type: GET_EMPLOYEES.REQUEST });
const getEmployeesSuccess = payload => ({ type: GET_EMPLOYEES.SUCCESS, payload });
const getEmployeesFailure = error => ({ type: GET_EMPLOYEES.FAILURE, error });

const getRolesRequest = () => ({ type: GET_ROLES.REQUEST });
const getRolesSuccess = payload => ({ type: GET_ROLES.SUCCESS, payload });
const getRolesFailure = error => ({ type: GET_ROLES.FAILURE, error });

const getEmployeeDetailRequest = () => ({ type: GET_EMPLOYEE_DETAIL.REQUEST });
const getEmployeeDetailSuccess = payload => ({ type: GET_EMPLOYEE_DETAIL.SUCCESS, payload });
const getEmployeeDetailFailure = error => ({ type: GET_EMPLOYEE_DETAIL.FAILURE, error })

const getRoleDetailRequest = () => ({ type: GET_ROLE_DETAIL.REQUEST });
const getRoleDetailSuccess = payload => ({ type: GET_ROLE_DETAIL.SUCCESS, payload });
const getRoleDetailFailure = error => ({ type: GET_ROLE_DETAIL.FAILURE, error });

export const getEmployees = (params, isNext) => {
  return (dispatch, getState) => {
    dispatch(getEmployeesRequest());
    return axios.get(Pathes.Employees.list + getQuery(params))
      .then(res => {
        const {status, data} = res;
        const message = getMessage(data);
        if (status === 200) {
          const prevData = getState().employeeStore.employees.data;
          if (!isNext || !prevData) {
            dispatch(getEmployeesSuccess(data));
            return { data, success: true }
          }

          const updatedData = {
            total_count: data.total_count,
            total_pages: data.total_pages,
            list: [ ...prevData.list, ...data.list]
          }
          dispatch(getEmployeesSuccess(updatedData));
          return { ...updatedData, success: true }
        }
        throw new Error(message)})
      .catch(e => dispatch(getEmployeesFailure(e.message)));
  }
}

export const getEmployeeInfo = userID => {
  return dispatch => {
    return axios.get(Pathes.Employees.info(userID))
      .then(res => {
        const {status, data} = res;
        const message = getMessage(data);
        if (status === 200) {
          dispatch({ type: GET_EMPLOYEE_INFO, employee: data });
          return { data, success: true }
        }
        throw new Error(message)})
      .catch(e => ({ error: e.message }));
  }
}

export const addEmployee = data => {
  return () => {
    return axios.post(Pathes.Employees.addEmployee, data)
      .then(res => {
        const {status, data} = res;
        const message = getMessage(data);
        if (status === 201) {
          Notify.success({ text: 'Вы добавили нового сотрудника'})
          return { data, success: true }
        }

        if (status === 406 && data.errors && data.errors.non_field_errors[0] && data.errors.non_field_errors[0] === 'The fields organization, user must make a unique set.') {
          Notify.info({ text: 'Данный сотрудник уже добавлен' })
        }

        throw new Error(message)})
      .catch(e => ({ error: e.message }));
  }
}

export const removeEmployee = id => {
  return () => {
    return axios.delete(Pathes.Employees.employee(id))
      .then(res => {
        const {status, data} = res;
        const message = getMessage(data);
        if (status === 204) {
          Notify.success({ text: 'Вы успешно уволили сотрудника'})
          return { data, success: true }
        }
        throw new Error(message)})
      .catch(e => ({ error: e.message }));
  }
}

export const updateEmployeeRole = (employeeID, role) => {
  return () => {
    return axios.put(Pathes.Employees.employee(employeeID), { role })
      .then(res => {
        const {status, data} = res;
        const message = getMessage(data);
        if (status === 200) {
          Notify.success({ text: 'Вы изменили должность сотрудника'})
          return { data, success: true }
        }
        throw new Error(message)})
      .catch(e => ({ error: e.message }));
  }
}

export const setOrganizationOwner = (orgID, userID) => {
  return () => {
    return axios.post(Pathes.Employees.transferOwnership, { organization: orgID, new_owner: userID })
      .then(res => {
        const {status, data} = res;
        const message = getMessage(data);
        if (status === 200) {
          Notify.success({ text: 'Вы передали права собственника'})
          return { data, success: true }
        }
        if (status === 403) { Notify.info({ text: 'У Вас нет прав передачи собственника'}) }
        throw new Error(message)})
      .catch(e => ({ error: e.message }))
  }
}

export const createRole = data => {
  return () => {
    return axios.post(Pathes.Employees.roles, data).then(res => {
      const {status, data} = res;
      const message = getMessage(data);
      if (status === 201) {
        return { data, success: true }
      }
      throw new Error(message)})
      .catch(e => ({ error: e.message }));
  }
}

export const getRoles = (params, isNext) => {
  return (dispatch, getState) => {
    dispatch(getRolesRequest());
    return axios.get(Pathes.Employees.roles + getQuery(params))
      .then(res => {
        const {status, data} = res;
        const message = getMessage(data);
        if (status === 200) {
          const prevData = getState().employeeStore.roles.data;
          if (!isNext || !prevData) {
            dispatch(getRolesSuccess(data));
            return { data, success: true }
          }

          const updatedData = {
            total_count: data.total_count,
            total_pages: data.total_pages,
            list: [ ...prevData.list, ...data.list]
          }
          dispatch(getRolesSuccess(updatedData));
          return { ...updatedData, success: true }
        }
        throw new Error(message)})
      .catch(e => dispatch(getRolesFailure(e.message)));
  }
}

export const getRoleDetail = id => {
  return dispatch => {
    dispatch(getRoleDetailRequest());
    return axios.get(Pathes.Employees.roleDetail(id))
      .then(res => {
        const {status, data} = res;
        const message = getMessage(data);
        if (status === 200) {
          dispatch(getRoleDetailSuccess(data));
          return { data, success: true }
        }
        throw new Error(message)})
      .catch(e => getRoleDetailFailure(e.message));
  }
}

export const updateRole = (id, payload) => {
  return () => {
    return axios.put(Pathes.Employees.roleDetail(id), payload)
      .then(res => {
        const {status, data} = res;
        const message = getMessage(data);
        if (status === 200) {
          Notify.success({ text: 'Должность успешно обновлена' })
          return { data, success: true }
        }
        throw new Error(message)})
      .catch(e => ({ error: e.message }));
  }
}

export const removeRole = id => {
  return () => {
    return axios.delete(Pathes.Employees.roleDetail(id))
      .then(res => {
        const {status, data} = res;
        const message = getMessage(data);
        if (status === 204) {
          Notify.success({ text: 'Вы успешно удалили должность' })
          return { data, success: true }
        }
        throw new Error(message)})
      .catch(e => ({ error: e.message }));
  }
}

export const getEmployeeDetail = (employeeID, redirect) => {
  return (dispatch) => {
    dispatch(getEmployeeDetailRequest());
    return axios.get(Pathes.Employees.employee(employeeID))
      .then(res => {
        const {status, data} = res;
        const message = getMessage(data);
        if (status === 200) {
          dispatch(getEmployeeDetailSuccess(data));
          return { data, success: true }
        }
        redirect && redirect();
        throw new Error(message)})
      .catch(e => dispatch(getEmployeeDetailFailure(e.message)));
  }
}