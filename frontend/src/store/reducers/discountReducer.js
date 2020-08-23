import {SET_PRE_ORGANIZATION} from "../actions/actionTypes";

const initialState = {
  preOrganization: null
};

const discountReducer = (state = initialState, action) => {
  switch (action.type) {
    case SET_PRE_ORGANIZATION:
      return { ...state, preOrganization: action.organization }
    default:
    return state;
  }
};

export default discountReducer;