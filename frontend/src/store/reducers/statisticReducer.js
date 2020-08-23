import {METADATA} from '../../common/metadata';
import {
  GET_ALL_STATISTICS, GET_ORG_PARTNERS_STATISTIC_SUMMARY, GET_ORG_STATISTIC_SUMMARY,
  GET_RECEIPT_DETAIL,
  GET_RECEIPTS,
  GET_STATISTIC_SUMMARY
} from '../actionTypes/statisticTypes';

const initialState = {
  summary: null,
  orgSummary: null,
  orgPartnersSummary: null,
  allStatistics: { ...METADATA.default, data: null },
  receipts: { ...METADATA.default, data: null },
  receiptDetail: { ...METADATA.default, data: null },
};

const statisticReducer = (state = initialState, action) => {
  switch (action.type) {
    case GET_STATISTIC_SUMMARY:
      return { ...state, summary: action.payload };
    case GET_ORG_STATISTIC_SUMMARY:
      return { ...state, orgSummary: action.payload };
    case GET_ORG_PARTNERS_STATISTIC_SUMMARY:
      return { ...state, orgPartnersSummary: action.payload };
    case GET_ALL_STATISTICS.REQUEST:
      return { ...state, allStatistics: { ...state.allStatistics, ...METADATA.request }};
    case GET_ALL_STATISTICS.SUCCESS:
      return { ...state, allStatistics: { ...METADATA.success, data: action.payload }};
    case GET_ALL_STATISTICS.FAILURE:
      return { ...state, allStatistics: { ...state.allStatistics, ...METADATA.error, error: action.error }};
    case GET_RECEIPTS.REQUEST:
      return { ...state, receipts: { ...state.receipts, ...METADATA.request }};
    case GET_RECEIPTS.SUCCESS:
      return { ...state, receipts: { ...METADATA.success, data: action.data }};
    case GET_RECEIPTS.FAILURE:
      return { ...state, receipts: { ...state.receipts, ...METADATA.error, error: action.error }};
    case GET_RECEIPT_DETAIL.REQUEST:
      return { ...state, receiptDetail: { ...state.receiptDetail, ...METADATA.request }};
    case GET_RECEIPT_DETAIL.SUCCESS:
      return { ...state, receiptDetail: { ...METADATA.success, data: action.data }};
    case GET_RECEIPT_DETAIL.FAILURE:
      return { ...state, receiptDetail: { ...state.receiptDetail, ...METADATA.error, error: action.error }};
    default:
      return state;
  }
};

export default statisticReducer;