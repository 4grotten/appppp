import {METADATA} from '../../common/metadata';
import {GET_PHONE_NUMBERS, GET_SOCIALS} from '../actions/actionTypes';

const initialState = {
  myProfile: {...METADATA.default, data: null},
  phoneNumbers: { ...METADATA.default, data: null},
  socialNetworks: { ...METADATA.default, data: null}
};

const profileReducer = (state = initialState, action) => {
  switch (action.type) {
    case GET_PHONE_NUMBERS.REQUEST:
      return { ...state, phoneNumbers: { ...state.phoneNumbers, ...METADATA.request } };
    case GET_PHONE_NUMBERS.SUCCESS:
      return { ...state, phoneNumbers: { ...state.phoneNumbers, ...METADATA.success, data: action.phones } };
    case GET_PHONE_NUMBERS.FAILURE:
      return { ...state, phoneNumbers: { ...state.phoneNumbers, ...METADATA.error } };

    case GET_SOCIALS.REQUEST:
      return { ...state, socialNetworks: { ...state.socialNetworks, ...METADATA.request } };
    case GET_SOCIALS.SUCCESS:
      return { ...state, socialNetworks: { ...state.socialNetworks, ...METADATA.success, data: action.socials } };
    case GET_SOCIALS.FAILURE:
      return { ...state, socialNetworks: { ...state.socialNetworks, ...METADATA.error } };
    default:
      return state;
  }
};

export default profileReducer;