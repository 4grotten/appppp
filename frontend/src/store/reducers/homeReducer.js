import {METADATA} from '../../common/metadata';
import {
  GET_HOME_ORGANIZATIONS,
  GET_LOCAL_BANNERS,
  GET_ORGS_BY_CATEGORIES, GET_SEARCH_RESULT,
  SELECT_CATEGORY
} from '../actionTypes/homeTypes';

const initialState = {
  homeOrganizations: { ...METADATA.default, data: null },
  localBanners: { ...METADATA.default, data: null },
  orgsByCategories: { ...METADATA.default, data: null },
  searchResult: { ...METADATA.default, data: null },
  selectedCategory: null,
};

const homeReducer = (state = initialState, action) => {
  switch (action.type) {
    case GET_HOME_ORGANIZATIONS.REQUEST:
      return { ...state, homeOrganizations: { ...state.homeOrganizations, ...METADATA.request }};
    case GET_HOME_ORGANIZATIONS.SUCCESS:
      return { ...state, homeOrganizations: { ...METADATA.success, data: action.payload }};
    case GET_HOME_ORGANIZATIONS.FAILURE:
      return { ...state, homeOrganizations: { ...state.homeOrganizations, ...METADATA.error, error: action.error }};
    case GET_LOCAL_BANNERS.REQUEST:
      return { ...state, localBanners: { ...state.localBanners, ...METADATA.request }};
    case GET_LOCAL_BANNERS.SUCCESS:
      return { ...state, localBanners: { ...METADATA.success, data: action.payload }};
    case GET_LOCAL_BANNERS.FAILURE:
      return { ...state, localBanners: { ...state.localBanners, ...METADATA.error, error: action.error }};
    case GET_ORGS_BY_CATEGORIES.REQUEST:
      return { ...state, orgsByCategories: { ...state.orgsByCategories, ...METADATA.request }};
    case GET_ORGS_BY_CATEGORIES.SUCCESS:
      return { ...state, orgsByCategories: { ...METADATA.success, data: action.payload }};
    case GET_ORGS_BY_CATEGORIES.FAILURE:
      return { ...state, orgsByCategories: { ...state.orgsByCategories, ...METADATA.error, error: action.error }};
    case GET_SEARCH_RESULT.REQUEST:
      return { ...state, searchResult: { ...state.searchResult, ...METADATA.request }};
    case GET_SEARCH_RESULT.SUCCESS:
      return { ...state, searchResult: { ...METADATA.success, data: action.payload }};
    case GET_SEARCH_RESULT.FAILURE:
      return { ...state, searchResult: { ...state.searchResult, ...METADATA.error, error: action.error }};
    case SELECT_CATEGORY:
      return { ...state, selectedCategory: action.category };
    default:
      return state;
  }
};

export default homeReducer;