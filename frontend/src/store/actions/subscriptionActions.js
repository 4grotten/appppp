import axios from '../../axios-api';
import Pathes from '../../common/pathes';
import {getMessage} from '../../common/helpers';
import {GET_ORG_SUBSCRIPTIONS} from '../actionTypes/subscriptionTypes';
import Notify from '../../components/Notification';
import {SUBSCRIBE_ORGANIZATION} from './actionTypes';
import qs from 'qs';

const getOrgSubscriptionsRequest = () => ({ type: GET_ORG_SUBSCRIPTIONS.REQUEST });
const getOrgSubscriptionsSuccess = payload => ({ type: GET_ORG_SUBSCRIPTIONS.SUCCESS, payload });
const getOrgSubscriptionsFailure = error => ({ type: GET_ORG_SUBSCRIPTIONS.FAILURE, error });

export const subscribeOrganization = orgID => {
  return (dispatch, getState) => {
    return axios.post(Pathes.Organization.subscribe, { organization: orgID }).then(
      res => {
        const {status, data} = res;
        const message = getMessage(data);
        if (status === 200) {
          Notify.success({text: data.data.is_subscribed ? 'Вы подписаны' : 'Вы отписались'});

          const prevData = getState().organizationStore.orgDetail.data;
          if (prevData) {
            let subscribersCount = prevData.subscribers;
            if (data.data.is_subscribed) {
              subscribersCount += 1;
            } else if (!!subscribersCount) {
              subscribersCount -= 1;
            }
            dispatch({type: SUBSCRIBE_ORGANIZATION, organization: {...prevData, is_subscribed: data.data.is_subscribed, subscribers: subscribersCount }})
          }

          return {...data, success: true, message};
        }
        throw new Error(message)
      }).catch(e => ({ error: e.message }))
  }
}

export const getOrgSubscriptions = (params, isNext)  => {
  return (dispatch, getState) => {
    const filteredParams = { ...params, unsubscribed: null };
    delete filteredParams.hasMore;
    delete filteredParams.unsubscribed;
    const query = `?${qs.stringify(filteredParams, { strictNullHandling: true, skipNulls: true })}`;
    dispatch(getOrgSubscriptionsRequest());
    return axios.get(Pathes.Subscriptions.getList + query).then(
      res => {
        const {status, data} = res;
        const message = getMessage(data);
        if (status === 200) {
          const prevData = getState().subscriptionStore.subscriptions.data;
          if (!isNext || !prevData) {
            dispatch(getOrgSubscriptionsSuccess(data));
            return {...data, success: true, message};
          }

          const updatedData = {
            total_count: data.total_count,
            total_pages: data.total_pages,
            list: [ ...prevData.list, ...data.list]
          }
          dispatch(getOrgSubscriptionsSuccess(updatedData));
          return {...updatedData, success: true, message};
        }

        throw new Error(message)
      }).catch(e => dispatch(getOrgSubscriptionsFailure(e.message))
    )
  }
}