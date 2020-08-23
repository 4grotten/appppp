import {METADATA} from '../../common/metadata';
import {GET_ORG_PARTNERS, GET_ORG_PARTNERSHIPS, GET_PARTNERSHIP_DETAIL} from '../actionTypes/partnerTypes';

const initialState = {
  orgPartners: { ...METADATA.default, data: null },
  orgPartnerships: { ...METADATA.default, data: null },
  partnershipDetail: { ...METADATA.default, data: null },
};

const partnerReducer = (state = initialState, action) => {
  switch (action.type) {
    case GET_ORG_PARTNERS.REQUEST:
      return { ...state, orgPartners: { ...state.orgPartners, ...METADATA.request }};
    case GET_ORG_PARTNERS.SUCCESS:
      return { ...state, orgPartners: { ...METADATA.success, data: action.payload }};
    case GET_ORG_PARTNERS.FAILURE:
      return { ...state, orgPartners: { ...state.orgPartners, ...METADATA.error, error: action.error }};
    case GET_ORG_PARTNERSHIPS.REQUEST:
      return { ...state, orgPartnerships: { ...state.orgPartnerships, ...METADATA.request }};
    case GET_ORG_PARTNERSHIPS.SUCCESS:
      return { ...state, orgPartnerships: { ...METADATA.success, data: action.payload }};
    case GET_ORG_PARTNERSHIPS.FAILURE:
      return { ...state, orgPartnerships: { ...state.orgPartnerships, ...METADATA.error, error: action.error }};
    case GET_PARTNERSHIP_DETAIL.REQUEST:
      return { ...state, partnershipDetail: { ...METADATA.request, data: null }};
    case GET_PARTNERSHIP_DETAIL.SUCCESS:
      return { ...state, partnershipDetail: { ...METADATA.success, data: action.payload }};
    case GET_PARTNERSHIP_DETAIL.FAILURE:
      return { ...state, partnershipDetail: { ...state.partnershipDetail, ...METADATA.error, error: action.error }};

    default:
      return state;
  }
};

export default partnerReducer;