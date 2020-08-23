import axios from '../../axios-api';
import Pathes from '../../common/pathes';
import {getMessage} from '../../common/helpers';
import {getQuery} from '../../common/utils';
import {GET_ORG_PARTNERS, GET_ORG_PARTNERSHIPS, GET_PARTNERSHIP_DETAIL} from '../actionTypes/partnerTypes';
import Notify from '../../components/Notification';

const getOrgPartnersRequest = () => ({ type: GET_ORG_PARTNERS.REQUEST });
const getOrgPartnersSuccess = payload => ({ type: GET_ORG_PARTNERS.SUCCESS, payload });
const getOrgPartnersFailure = error => ({ type: GET_ORG_PARTNERS.FAILURE, error });

const getOrgPartnershipsRequest = () => ({ type: GET_ORG_PARTNERSHIPS.REQUEST });
const getOrgPartnershipsSuccess = payload => ({ type: GET_ORG_PARTNERSHIPS.SUCCESS, payload });
const getOrgPartnershipsFailure = error => ({ type: GET_ORG_PARTNERSHIPS.FAILURE, error });

const getPartnershipDetailRequest = () => ({ type: GET_PARTNERSHIP_DETAIL.REQUEST });
const getPartnershipDetailSuccess = payload => ({ type: GET_PARTNERSHIP_DETAIL.SUCCESS, payload });
const getPartnershipDetailFailure = error => ({ type: GET_PARTNERSHIP_DETAIL.FAILURE, error });

export const getOrgPartners = (orgID, params, isNext) => {
  return (dispatch, getState) => {
    dispatch(getOrgPartnersRequest());
    return axios.get(Pathes.Partners.partners(orgID) + getQuery(params)).then(
      res => {
        const {status, data} = res;
        const message = getMessage(data);
        if (status === 200) {
          const prevData = getState().partnerStore.orgPartners.data;
          if (!isNext || !prevData) {
            dispatch(getOrgPartnersSuccess(data));
            return { ...data, success: true }
          }

          const updatedData = {
            total_count: data.total_count,
            total_pages: data.total_pages,
            list: [ ...prevData.list, ...data.list]
          }
          dispatch(getOrgPartnersSuccess(updatedData));
          return { ...updatedData, success: true }
        }

        throw new Error(message)
      }).catch(e => dispatch(getOrgPartnersFailure(e.message)));
  }
}

export const getOrgPartnerships = (orgID, params, isNext) => {
  return (dispatch, getState) => {
    dispatch(getOrgPartnershipsRequest());
    return axios.get(Pathes.Partners.partnerships(orgID) + getQuery(params)).then(
      res => {
        const {status, data} = res;
        const message = getMessage(data);
        if (status === 200) {
          const prevData = getState().partnerStore.orgPartnerships.data;
          if (!isNext || !prevData) {
            dispatch(getOrgPartnershipsSuccess(data));
            return { ...data, success: true }
          }

          const updatedData = {
            total_count: data.total_count,
            total_pages: data.total_pages,
            list: [ ...prevData.list, ...data.list]
          }
          dispatch(getOrgPartnershipsSuccess(updatedData));
          return { ...updatedData, success: true }
        }
        throw new Error(message)
      }).catch(e => dispatch(getOrgPartnershipsFailure(e.message)));
  }
}

export const createPartnership = payload => {
  return dispatch => {
    return axios.post(Pathes.Partners.createPartnership, payload).then(
      res => {
        const {status, data} = res;
        const message = getMessage(data);
        if (status === 200) {
          Notify.success({ text: 'Запрос на партнерство успешно отправлено'});
          return {...data, success: true };
        }
        throw new Error(message)
      }).catch(e => dispatch(getOrgPartnershipsFailure(e.message)));
  }
}

export const getPartnershipDetail = id => {
  return dispatch => {
    dispatch(getPartnershipDetailRequest());
    return axios.get(Pathes.Partners.partnershipDetail(id)).then(
      res => {
        const {status, data} = res;
        const message = getMessage(data);
        if (status === 200) {
          dispatch(getPartnershipDetailSuccess(data))
          return {...data, success: true};
        }
        throw new Error(message)
      }).catch(e => dispatch(getPartnershipDetailFailure(e.message)));
  }
}

export const setPartnershipPermissions = (id, payload) => {
  return () => {
    return axios.put(Pathes.Partners.partnershipDetail(id), payload).then(
      res => {
        const {status, data} = res;
        const message = getMessage(data);
        if (status === 200) {
          return {...data, success: true};
        }
        throw new Error(message)
      }).catch(e => ({ error: e.message }));
  }
}

export const rejectPartnership = id => {
  return () => {
    return axios.delete(Pathes.Partners.partnershipDetail(id)).then(
      res => {
        const {status, data} = res;
        const message = getMessage(data);
        if (status === 204) {
          Notify.success({ text: 'Вы отклонили партнерство'})
          return {...data, success: true};
        }
        throw new Error(message)
      }).catch(e => ({ error: e.message }));
  }
}