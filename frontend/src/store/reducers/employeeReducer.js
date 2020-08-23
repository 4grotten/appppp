import {METADATA} from '../../common/metadata';
import {
  GET_EMPLOYEE_DETAIL,
  GET_EMPLOYEE_INFO,
  GET_EMPLOYEES,
  GET_ROLE_DETAIL,
  GET_ROLES,
} from '../actionTypes/employeeTypes';

const initialState = {
  employees: { ...METADATA.default, data: null },
  employeeDetail: { ...METADATA.default, data: null },
  selectedEmployee: null,
  roles: { ...METADATA.default, data: null },
  roleDetail: { ...METADATA.default, data: null },
  invite: null,
};

const employeeReducer = (state = initialState, action) => {
  switch (action.type) {
    case GET_EMPLOYEES.REQUEST:
      return { ...state, employees: { ...state.employees, ...METADATA.request }};
    case GET_EMPLOYEES.SUCCESS:
      return { ...state, employees: { ...METADATA.success, data: action.payload }};
    case GET_EMPLOYEES.FAILURE:
      return { ...state, employees: { ...state.employees, ...METADATA.error, error: action.error }};
    case GET_ROLES.REQUEST:
      return { ...state, roles: { ...state.roles, ...METADATA.request }};
    case GET_ROLES.SUCCESS:
      return { ...state, roles: { ...METADATA.success, data: action.payload }};
    case GET_ROLES.FAILURE:
      return { ...state, roles: { ...state.roles, ...METADATA.error, error: action.error }};
    case GET_ROLE_DETAIL.REQUEST:
      return { ...state, roleDetail: { ...state.roleDetail, ...METADATA.request, data: null }};
    case GET_ROLE_DETAIL.SUCCESS:
      return { ...state, roleDetail: { ...METADATA.success, data: action.payload }};
    case GET_ROLE_DETAIL.FAILURE:
      return { ...state, roleDetail: { ...state.roleDetail, ...METADATA.error, error: action.error }};
    case GET_EMPLOYEE_INFO:
      return { ...state, invite: action.employee };
    case GET_EMPLOYEE_DETAIL.REQUEST:
      return { ...state, employeeDetail: { ...METADATA.request, data: null }};
    case GET_EMPLOYEE_DETAIL.SUCCESS:
      return { ...state, employeeDetail: { ...METADATA.success, data: action.payload }};
    case GET_EMPLOYEE_DETAIL.FAILURE:
      return { ...state, employeeDetail: { ...state.employeeDetail, ...METADATA.error, error: action.error }};
    default:
      return state;
  }
};

export default employeeReducer;