import axios from '../../axios-api';
import {push} from 'react-router-redux';
import Pathes from '../../common/pathes';
import Notify from '../../components/Notification';
import qs from 'qs';
import {getMessage} from '../../common/helpers';
import {getQuery} from '../../common/utils';
import {
  CREATE_ORG,
  GET_CARD_BACKGROUNDS,
  GET_ORG,
  GET_ORG_LIST, GET_ORG_RECEIPT_DETAIL, GET_ORG_RECEIPTS,
  GET_ORG_TYPES,
  TOGGLE_SHOW_CONTACT,
} from './actionTypes';
import {GET_ORG_FOLLOWERS} from '../actionTypes/organizationTypes';

const createOrgRequest = () => ({ type: CREATE_ORG.REQUEST });
const createOrgSuccess = org => ({ type: CREATE_ORG.SUCCESS, org });
const createOrgFailure = error => ({ type: CREATE_ORG.FAILURE, error });

const getOrgListRequest = () => ({ type: GET_ORG_LIST.REQUEST });
const getOrgListSuccess = list => ({ type: GET_ORG_LIST.SUCCESS, list });
const getOrgListFailure = error => ({ type: GET_ORG_LIST.FAILURE, error });

const getOrgRequest = () => ({ type: GET_ORG.REQUEST });
const getOrgSuccess = detail => ({ type: GET_ORG.SUCCESS, detail });
const getOrgFailure = error => ({ type: GET_ORG.FAILURE, error });

const getOrgTypesRequest = () => ({ type: GET_ORG_TYPES.REQUEST });
const getOrgTypesSuccess = types => ({ type: GET_ORG_TYPES.SUCCESS, types });
const getOrgTypesFailure = error => ({ type: GET_ORG_TYPES.FAILURE, error });

const getCardBackgroundsRequest = () => ({ type: GET_CARD_BACKGROUNDS.REQUEST });
const getCardBackgroundsSuccess = backgrounds => ({ type: GET_CARD_BACKGROUNDS.SUCCESS, backgrounds });
const getCardBackgroundsFailure = error => ({ type: GET_CARD_BACKGROUNDS.FAILURE, error });

const getOrgReceiptsRequest = () => ({ type: GET_ORG_RECEIPTS.REQUEST });
const getOrgReceiptsSuccess = payload => ({ type: GET_ORG_RECEIPTS.SUCCESS, payload });
const getOrgReceiptsFailure = error => ({ type: GET_ORG_RECEIPTS.FAILURE, error });

const getOrgReceiptDetailRequest = () => ({ type: GET_ORG_RECEIPT_DETAIL.REQUEST });
const getOrgReceiptDetailSuccess = payload => ({ type: GET_ORG_RECEIPT_DETAIL.SUCCESS, payload });
const getOrgReceiptDetailFailure = error => ({ type: GET_ORG_RECEIPT_DETAIL.FAILURE, error });

const getOrgFollowersRequest = () => ({ type: GET_ORG_FOLLOWERS.REQUEST });
const getOrgFollowersSuccess = payload => ({ type: GET_ORG_FOLLOWERS.SUCCESS, payload });
const getOrgFollowersFailure = error => ({ type: GET_ORG_FOLLOWERS.FAILURE, error });

export const getOrganizationsList = (params, isNext) => {
  return (dispatch, getState) => {
    const filteredParams = { ...params };
    delete filteredParams.hasMore;

    const query = `?${qs.stringify(filteredParams, { strictNullHandling: true, skipNulls: true })}`;
    dispatch(getOrgListRequest())
    return axios.get(Pathes.Organization.list + query).then(
      res => {
        const {status, data} = res;
        const message = getMessage(data);
        if (status === 200) {
          const prevData = getState().organizationStore.orgList.data;
          if (!isNext || !prevData) {
            dispatch(getOrgListSuccess(data));
            return {...data, success: true, message};
          }

          const updatedData = {
            total_count: data.total_count,
            total_pages: data.total_pages,
            list: [ ...prevData.list, ...data.list]
          }
          dispatch(getOrgListSuccess(updatedData));
          return {...updatedData, success: true, message};
        }

        Notify.info({text: message})
        throw new Error(message)
      }).catch(e => dispatch(getOrgListFailure(e.message)));
  }
}

export const getOrganizationDetail = id => {
  return dispatch => {
    dispatch(getOrgRequest())
    return axios.get(Pathes.Organization.get(id)).then(
      res => {
        const {status, data} = res;
        const message = getMessage(data);
        if (status === 200) {
          dispatch(getOrgSuccess(data));
          return {...data, success: true, message};
        }

        dispatch(push('/profile'));
        throw new Error(message)
      }).catch(e => dispatch(getOrgFailure(e.message)));
  }
}

export const createOrganization = data => {
  return dispatch => {
    dispatch(createOrgRequest())
    return axios.post(Pathes.Organization.create, data).then(
      res => {
        const {status, data} = res;
        const message = getMessage(data);
        if (status === 201) {
          dispatch(createOrgSuccess(data));
          Notify.success({text: 'Организация успешно создана'});
          return {...data, success: true, message};
        }

        Notify.info({text: 'Не удалось создать организацию'});
        throw new Error(message)
      }).catch(e => dispatch(createOrgFailure(e.message)));
  }
};

export const setOrganizationPhones = (data, id) => {
  return () => {
    return axios.post(Pathes.Organization.setPhones(id), data).then(
      res => {
        const {status, data} = res;
        const message = getMessage(data);
        if (status === 200) {
          return {...data, success: true, message};
        }

        Notify.info({text: message})
        throw new Error(message)
      }).catch(e => ({ error: e.message }));
  }
};

export const setOrganizationSocials = (data, id) => {
  return () => {
    return axios.post(Pathes.Organization.setSocials(id), data).then(
      res => {
        const {status, data} = res;
        const message = getMessage(data);
        if (status === 200) {
          return {...data, success: true, message};
        }

        throw new Error(message)
      }).catch(e => ({ error: e.message }));
  }
};

export const getOrganizationTypes = () => {
  return dispatch => {
    dispatch(getOrgTypesRequest())
    return axios.get(Pathes.Organization.types).then(
      res => {
        const {status, data} = res;
        const message = getMessage(data);
        if (status === 200) {
          dispatch(getOrgTypesSuccess(data));
          return {...data, success: true, message};
        }

        Notify.info({text: message})
        throw new Error(message)
      }).catch(e => dispatch(getOrgTypesFailure(e.message)));
  }
}

export const editOrganization = (id, payload) => {
  return dispatch => {
    return axios.put(Pathes.Organization.edit(id), payload).then(
      res => {
        const {status, data} = res;
        const message = getMessage(data);
        if (status === 200) {
          Notify.success({text: 'Вы успешно обновили данные организации'});
          dispatch(push(`/organizations/${id}`));
          dispatch(getOrgSuccess(data));
          return {...data, success: true, message};
        }

        Notify.info({text: message})
        throw new Error(message)
      }).catch(e => ({ error: e.message }));
  }
}

export const toggleShowContact = () => {
  return (dispatch, getState) => {
    const data = getState().organizationStore.orgDetail.data;
    if (data) {
      const current = data.show_contacts;
      const detail = {
        ...data,
        show_contacts: !current
      }

      dispatch({ type: TOGGLE_SHOW_CONTACT, detail })
    }
  }
}

export const createOrganizationDiscount = payload => {
  return () => {
    return axios.post(Pathes.Organization.createDiscount, payload).then(
      res => {
        const {status, data} = res;
        const message = getMessage(data);
        if (status === 201) {
          Notify.success({text: 'Вы успешно создали карты организации'});
          return {...data, success: true, message};
        }

        throw new Error(message)
      }).catch(e => ({ error: e.message }))
  }
}

export const bulkUpdateOrgDiscounts = payload => {
  return () => {
    return axios.post(Pathes.Organization.bulkUpdateDiscounts, payload).then(
      res => {
        const {status, data} = res;
        const message = getMessage(data);
        if (status === 200) {
          Notify.success({text: 'Вы успешно обновили карты организации'});
          return {...data, success: true, message};
        }

        throw new Error(message)
      }).catch(e => ({ error: e.message }))
  }
}

export const bulkDeleteOrgDiscounts = payload => {
  return () => {
    return axios.post(Pathes.Organization.bulkDeleteDiscounts, payload).then(
      res => {
        const {status, data} = res;
        const message = getMessage(data);
        if (status === 200) {
          Notify.success({text: 'Вы успешно удалили карты организации'});
          return {...data, success: true, message};
        }

        throw new Error(message)
      }).catch(e => ({ error: e.message }))
  }
}

export const editDiscountImage = (cardID, image_id, orgID) => {
  return dispatch => {
    return axios.put(Pathes.Organization.discountImage(cardID), { image_id }).then(
      res => {
        const {status, data} = res;
        const message = getMessage(data);
        if (status === 200) {
          orgID && dispatch(getOrganizationDetail(orgID));
          Notify.success({ text: 'Фон успешно изменён' });
          return {...data, success: true, message};
        }

        throw new Error(message)
      }).catch(e => ({ error: e.message }))
  }
}

export const getCardBackgrounds = () => {
  return dispatch => {
    dispatch(getCardBackgroundsRequest());
    return axios.get(Pathes.Organization.cardBackgrounds).then(
      res => {
        const {status, data} = res;
        const message = getMessage(data);
        if (status === 200) {
          dispatch(getCardBackgroundsSuccess(data))
          return {...data, success: true, message};
        }

        throw new Error(message)
      }).catch(e => getCardBackgroundsFailure(e.message))
  }
}

export const getOrgReceipts = (params, isNext) => {
  return (dispatch, getState) => {
    dispatch(getOrgReceiptsRequest())
    return axios.get(Pathes.Organization.receipts + getQuery(params)).then(
      res => {
        const {status, data} = res;
        const message = getMessage(data);
        if (status === 200) {
          const prevData = getState().organizationStore.orgReceipts.data;
          if (!isNext || !prevData) {
            dispatch(getOrgReceiptsSuccess(data));
            return {...data, success: true, message};
          }

          const updatedData = {
            total_count: data.total_count,
            total_pages: data.total_pages,
            list: [ ...prevData.list, ...data.list]
          }
          dispatch(getOrgReceiptsSuccess(updatedData));
          return {...updatedData, success: true, message};
        }

        throw new Error(message)
      }).catch(e => dispatch(getOrgReceiptsFailure(e.message)));
  }
}


export const getOrgReceiptDetail = id => {
  return dispatch => {
    dispatch(getOrgReceiptDetailRequest());
    return axios.get(Pathes.Organization.receiptDetail(id)).then(
      res => {
        const {status, data} = res;
        const message = getMessage(data);
        if (status === 200) {
          dispatch(getOrgReceiptDetailSuccess(data))
          return {...data, success: true, message};
        }

        throw new Error(message)
      }).catch(e => getOrgReceiptDetailFailure(e.message))
  }
}

export const removeReceipt = id => {
  return () => {
    return axios.delete(Pathes.Organization.receiptDetail(id)).then(
      res => {
        const {status} = res;
        if (status === 204) {
          Notify.success({ text: `Чек ${id} успешно удалён`});
          return {id, success: true};
        }
        throw new Error('Транзакция не найдена')
      }).catch(e => ({ error: e.message }))
  }
}

export const getOrgFollowers = (orgID, params, isNext) => {
  return (dispatch, getState) => {
    dispatch(getOrgFollowersRequest());
    return axios.get(Pathes.Organization.followers(orgID) + getQuery(params)).then(
      res => {
        const {status, data} = res;
        const message = getMessage(data);
        if (status === 200) {
          const prevData = getState().organizationStore.orgFollowers.data;
          if (!isNext || !prevData) {
            dispatch(getOrgFollowersSuccess(data));
            return { ...data, success: true }
          }

          const updatedData = {
            total_count: data.total_count,
            total_pages: data.total_pages,
            list: [ ...prevData.list, ...data.list]
          }
          dispatch(getOrgFollowersSuccess(updatedData));
          return { ...updatedData, success: true }
        }

        throw new Error(message)
      }).catch(e => dispatch(getOrgFollowersFailure(e.message)));
  }
}