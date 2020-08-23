import axios from '../../axios-api';
import Pathes from '../../common/pathes';
import qs from 'qs';
import {getMessage} from '../../common/helpers';
import {getQuery} from '../../common/utils';
import {
  GET_HOME_ORGANIZATIONS,
  GET_LOCAL_BANNERS,
  GET_ORGS_BY_CATEGORIES, GET_SEARCH_RESULT,
  SELECT_CATEGORY
} from '../actionTypes/homeTypes';

const getHomeOrganizationsRequest = () => ({ type: GET_HOME_ORGANIZATIONS.REQUEST });
const getHomeOrganizationsSuccess = payload => ({ type: GET_HOME_ORGANIZATIONS.SUCCESS, payload });
const getHomeOrganizationsFailure = error => ({ type: GET_HOME_ORGANIZATIONS.FAILURE, error });

const getOrgsByCategoriesRequest = () => ({ type: GET_ORGS_BY_CATEGORIES.REQUEST });
const getOrgsByCategoriesSuccess = payload => ({ type: GET_ORGS_BY_CATEGORIES.SUCCESS, payload });
const getOrgsByCategoriesFailure = error => ({ type: GET_ORGS_BY_CATEGORIES.FAILURE, error });

const getSearchResultRequest = () => ({ type: GET_SEARCH_RESULT.REQUEST });
const getSearchResultSuccess = payload => ({ type: GET_SEARCH_RESULT.SUCCESS, payload });
const getSearchResultFailure = error => ({ type: GET_SEARCH_RESULT.FAILURE, error });

const getLocalBannersRequest = () => ({ type: GET_LOCAL_BANNERS.REQUEST });
const getLocalBannersSuccess = payload => ({ type: GET_LOCAL_BANNERS.SUCCESS, payload });
const getLocalBannersFailure = error => ({ type: GET_LOCAL_BANNERS.FAILURE, error });

export const getHomeOrganizations = (params, isNext) => {
  return (dispatch, getState) => {
    const filteredParams = { ...params };
    delete filteredParams.hasMore;
    const query = `?${qs.stringify(filteredParams)}`;
    dispatch(getHomeOrganizationsRequest());
    return axios.get(Pathes.Home.homeOrganizations + query).then(
      res => {
        const {status, data} = res;
        const message = getMessage(data);
        if (status === 200) {
          const prevData = getState().homeStore.homeOrganizations.data;
          if (!isNext || !prevData) {
            dispatch(getHomeOrganizationsSuccess(data));
            return { ...data, success: true }
          }

          const updatedData = {
            total_count: data.total_count,
            total_pages: data.total_pages,
            list: [ ...prevData.list, ...data.list]
          }
          dispatch(getHomeOrganizationsSuccess(updatedData));
          return { ...updatedData, success: true }
        }

        throw new Error(message)
      }).catch(e => dispatch(getHomeOrganizationsFailure(e.message)));
  }
}

export const getOrgsByCategories = (params, isNext) => {
  return (dispatch, getState) => {
    const filteredParams = { ...params };
    delete filteredParams.hasMore;
    const query = `?${qs.stringify(filteredParams, { strictNullHandling: true, skipNulls: true })}`;
    dispatch(getOrgsByCategoriesRequest());
    return axios.get(Pathes.Home.orgsByCategories + query).then(
      res => {
        const {status, data} = res;
        const message = getMessage(data);
        if (status === 200) {
          const prevData = getState().homeStore.orgsByCategories.data;
          if (!isNext || !prevData) {
            dispatch(getOrgsByCategoriesSuccess(data));
            return { ...data, success: true }
          }

          const updatedData = {
            total_count: data.total_count,
            total_pages: data.total_pages,
            list: [ ...prevData.list, ...data.list]
          }
          dispatch(getOrgsByCategoriesSuccess(updatedData));
          return { ...updatedData, success: true }
        }

        throw new Error(message)
      }).catch(e => dispatch(getOrgsByCategoriesFailure(e.message)));
  }
}

export const getLocalBanners = () => {
  return dispatch => {
    dispatch(getLocalBannersRequest());
    return axios.get(Pathes.Home.localBanners).then(
      res => {
        const {status, data} = res;
        const message = getMessage(data);
        if (status === 200) {
          dispatch(getLocalBannersSuccess(data));
          return { ...data, success: true }
        }

        throw new Error(message)
      }).catch(e => dispatch(getLocalBannersFailure(e.message)));
  }
}

export const getCategoryDetail = id => {
  return dispatch => {
    return axios.get(Pathes.Home.getCategoryDetail(id)).then(
      res => {
        const {status, data} = res;
        if (status === 200) {
          dispatch(selectCategory(data));
          return { ...data, success: true }
        }
        throw new Error(message)
      }).catch(e => ({ error: e.message }));
  }
}

export const selectCategory = category => {
  return dispatch => dispatch({ type: SELECT_CATEGORY, category })
}

export const getSearchResult = (params, isNext) => {
  return (dispatch, getState) => {
    dispatch(getSearchResultRequest());
    return axios.get(Pathes.Home.search + getQuery(params)).then(
      res => {
        const {status, data} = res;
        if (status === 200) {
          const prevData = getState().homeStore.searchResult.data;
          if (!isNext || !prevData) {
            dispatch(getSearchResultSuccess(data));
            return { ...data, success: true }
          }

          const updatedData = {
            total_count: data.total_count,
            total_pages: data.total_pages,
            list: [ ...prevData.list, ...data.list]
          }
          dispatch(getSearchResultSuccess(updatedData));
          return { ...updatedData, success: true }
        }

        throw new Error('Не удалось получить')
      }).catch(e => dispatch(getSearchResultFailure(e.message)));
  }
}