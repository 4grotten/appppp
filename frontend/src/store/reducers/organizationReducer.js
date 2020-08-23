import {METADATA} from '../../common/metadata';
import {
  GET_CARD_BACKGROUNDS,
  GET_ORG,
  GET_ORG_LIST, GET_ORG_RECEIPT_DETAIL, GET_ORG_RECEIPTS,
  GET_ORG_TYPES,
  SUBSCRIBE_ORGANIZATION,
  TOGGLE_SHOW_CONTACT
} from '../actions/actionTypes';
import {GET_ORG_FOLLOWERS} from '../actionTypes/organizationTypes';

const initialState = {
  orgTypes: { ...METADATA.default, data: null },
  orgList: { ...METADATA.default, data: null },
  orgDetail: { ...METADATA.default, data: null },
  orgReceipts: { ...METADATA.default, data: null },
  cardBackgrounds: { ...METADATA.default, data: null },
  orgReceiptDetail: { ...METADATA.default, data: null },
  orgFollowers: { ...METADATA.default, data: null },
};

const organizationReducer = (state = initialState, action) => {
  switch (action.type) {
    case GET_ORG_TYPES.REQUEST:
      return { ...state, orgTypes: { ...state.orgTypes, ...METADATA.request } };
    case GET_ORG_TYPES.SUCCESS:
      return { ...state, orgTypes: { ...state.orgTypes, ...METADATA.success, data: action.types } };
    case GET_ORG_TYPES.FAILURE:
      return { ...state, orgTypes: { ...state.orgTypes, ...METADATA.error } };
    case GET_ORG.REQUEST:
      return { ...state, orgDetail: { ...state.orgDetail, ...METADATA.request } };
    case GET_ORG.SUCCESS:
      return { ...state, orgDetail: { ...state.orgDetail, ...METADATA.success, data: action.detail } };
    case GET_ORG.FAILURE:
      return { ...state, orgDetail: { ...state.orgDetail, ...METADATA.error } };
    case GET_ORG_LIST.REQUEST:
      return { ...state, orgList: { ...state.orgList, ...METADATA.request } };
    case GET_ORG_LIST.SUCCESS:
      return { ...state, orgList: { ...state.orgList, ...METADATA.success, data: action.list } };
    case GET_ORG_LIST.FAILURE:
      return { ...state, orgList: { ...state.orgList, ...METADATA.error } };
    case TOGGLE_SHOW_CONTACT:
      return { ...state, orgDetail: { ...state.orgDetail, data: action.detail } }
    case GET_CARD_BACKGROUNDS.REQUEST:
      return { ...state, cardBackgrounds: { ...state.cardBackgrounds, ...METADATA.request } };
    case GET_CARD_BACKGROUNDS.SUCCESS:
      return { ...state, cardBackgrounds: { ...state.cardBackgrounds, ...METADATA.success, data: action.backgrounds } };
    case GET_CARD_BACKGROUNDS.FAILURE:
      return { ...state, cardBackgrounds: { ...state.cardBackgrounds, ...METADATA.error } };
    case SUBSCRIBE_ORGANIZATION:
      return { ...state, orgDetail: { ...state.orgDetail, data: action.organization }};
    case GET_ORG_RECEIPTS.REQUEST:
      return { ...state, orgReceipts: { ...state.orgReceipts, ...METADATA.request } };
    case GET_ORG_RECEIPTS.SUCCESS:
      return { ...state, orgReceipts: { ...METADATA.success, data: action.payload } };
    case GET_ORG_RECEIPTS.FAILURE:
      return { ...state, orgReceipts: { ...state.orgReceipts, ...METADATA.error } };
    case GET_ORG_RECEIPT_DETAIL.REQUEST:
      return { ...state, orgReceiptDetail: { ...state.orgReceiptDetail, ...METADATA.request } };
    case GET_ORG_RECEIPT_DETAIL.SUCCESS:
      return { ...state, orgReceiptDetail: { ...METADATA.success, data: action.payload } };
    case GET_ORG_RECEIPT_DETAIL.FAILURE:
      return { ...state, orgReceiptDetail: { ...state.orgReceiptDetail, ...METADATA.error } };
    case GET_ORG_FOLLOWERS.REQUEST:
      return { ...state, orgFollowers: { ...state.orgFollowers, ...METADATA.request }};
    case GET_ORG_FOLLOWERS.SUCCESS:
      return { ...state, orgFollowers: { ...METADATA.success, data: action.payload }};
    case GET_ORG_FOLLOWERS.FAILURE:
      return { ...state, orgFollowers: { ...state.orgFollowers, ...METADATA.error, error: action.error }};

    default:
      return state;
  }
};

export default organizationReducer;