import axios from '../../axios-api';
import Pathes from '../../common/pathes';
import {getQuery} from '../../common/utils';
import {getMessage} from '../../common/helpers';
import {
  GET_ALL_STATISTICS, GET_ORG_PARTNERS_STATISTIC_SUMMARY, GET_ORG_STATISTIC_SUMMARY,
  GET_RECEIPT_DETAIL,
  GET_RECEIPTS,
  GET_STATISTIC_SUMMARY
} from '../actionTypes/statisticTypes';

const getAllStatisticsRequest = () => ({ type: GET_ALL_STATISTICS.REQUEST });
const getAllStatisticsSuccess = payload => ({ type: GET_ALL_STATISTICS.SUCCESS, payload });
const getAllStatisticsFailure = error => ({ type: GET_ALL_STATISTICS.FAILURE, error });

const getReceiptsRequest = () => ({ type: GET_RECEIPTS.REQUEST });
const getReceiptsSuccess = data => ({ type: GET_RECEIPTS.SUCCESS, data });
const getReceiptsFailure = error => ({ type: GET_RECEIPTS.FAILURE, error });

const getReceiptDetailRequest = () => ({ type: GET_RECEIPT_DETAIL.REQUEST });
const getReceiptDetailSuccess = data => ({ type: GET_RECEIPT_DETAIL.SUCCESS, data });
const getReceiptDetailFailure = error => ({ type: GET_RECEIPT_DETAIL.FAILURE, error });

export const getStatisticSummary = params => {
  return dispatch => {
    return axios.get(Pathes.Statistics.summary + getQuery(params)).then(
      res => {
        const {status, data} = res;
        const message = getMessage(data);
        if (status === 200) {
          dispatch({ type: GET_STATISTIC_SUMMARY, payload: data });
          return {...data, success: true, message};
        }

        throw new Error(message)
      }).catch(e => ({ error: e.message }));
  }
}

export const getOrgStatisticSummary = (id, params) => {
  return dispatch => {
    return axios.get(Pathes.Statistics.orgSummary(id) + getQuery(params)).then(
      res => {
        const {status, data} = res;
        const message = getMessage(data);
        if (status === 200) {
          dispatch({ type: GET_ORG_STATISTIC_SUMMARY, payload: data });
          return {...data, success: true, message};
        }

        throw new Error(message)
      }).catch(e => ({ error: e.message }));
  }
}

export const getOrgPartnerStatisticSummary = (orgID, params) => {
  return dispatch => {
    return axios.get(Pathes.Statistics.partnerStatistics(orgID) + getQuery(params)).then(
      res => {
        const {status, data} = res;
        const message = getMessage(data);
        if (status === 200) {
          dispatch({ type: GET_ORG_PARTNERS_STATISTIC_SUMMARY, payload: data });
          return {...data, success: true, message};
        }

        throw new Error(message)
      }).catch(e => ({ error: e.message }));
  }
}

export const getAllStatistics = (params, isNext) => {
  return (dispatch, getState) => {
    dispatch(getAllStatisticsRequest())
    return axios.get(Pathes.Statistics.allStatistics + getQuery(params)).then(
      res => {
        const {status, data} = res;
        const message = getMessage(data);
        if (status === 200) {
          const prevData = getState().statisticStore.allStatistics.data;
          if (!isNext || !prevData) {
            dispatch(getAllStatisticsSuccess(data));
            return {...data, success: true, message};
          }

          const updatedData = {
            total_count: data.total_count,
            total_pages: data.total_pages,
            list: [ ...prevData.list, ...data.list]
          }
          dispatch(getAllStatisticsSuccess(updatedData));
          return {...updatedData, success: true, message};
        }

        throw new Error(message)
      }).catch(e => dispatch(getAllStatisticsFailure(e.message)));
  }
};

export const getReceipts = (params, isNext) => {
  return (dispatch, getState) => {
    dispatch(getReceiptsRequest())
    return axios.get(Pathes.Statistics.receipts + getQuery(params)).then(
      res => {
        const {status, data} = res;
        const message = getMessage(data);
        if (status === 200) {
          const prevData = getState().statisticStore.receipts.data;
          if (!isNext || !prevData) {
            dispatch(getReceiptsSuccess(data));
            return {...data, success: true, message};
          }

          const updatedData = {
            total_count: data.total_count,
            total_pages: data.total_pages,
            list: [ ...prevData.list, ...data.list]
          }
          dispatch(getReceiptsSuccess(updatedData));
          return {...updatedData, success: true, message};
        }

        throw new Error(message)
      }).catch(e => dispatch(getReceiptsFailure(e.message)));
  }
}

export const getReceiptDetail = id => {
  return dispatch => {
    dispatch(getReceiptDetailRequest())
    return axios.get(Pathes.Statistics.receiptDetail(id)).then(
      res => {
        const {status, data} = res;
        const message = getMessage(data);
        if (status === 200) {
          dispatch(getReceiptDetailSuccess(data));
          return {...data, success: true, message};
        }

        throw new Error(message)
      }).catch(e => dispatch(getReceiptDetailFailure(e.message)));
  }
}

export const getOrganizationTitle = id => {
  return () => {
    return axios.get(Pathes.Statistics.getOrgTitle(id)).then(
      res => {
        const {status, data} = res;
        const message = getMessage(data);
        if (status === 200) {
          return {...data, success: true, message};
        }

        throw new Error(message)
      }).catch(e => ({ error: e.message, success: false }));
  }
}