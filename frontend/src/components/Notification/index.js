import * as React from 'react';
import * as classnames from 'classnames';
import { toast } from 'react-toastify';
import {CloseButton} from '../UI/Icons';
import PartnershipRequestToast from '../PartnershipRequestToast';
import './index.scss';

const toastDefaultConfig = {
  autoClose: 5000,
  closeButton: false,
  closeOnClick: true,
  draggable: true,
  position: 'top-center',
  hideProgressBar: true
};

let toastID;

class Notify {
  static info = (data, config) => {
    toast.dismiss(toastID);
    toast(<InfoToaster text={data.text} />, {
      ...toastDefaultConfig,
      ...config
    });
  }

  static success = (data, config) => {
    toast.dismiss(toastID);
    toastID = toast(<SuccessToaster text={data.text} />, {
      ...toastDefaultConfig,
      ...config
    });
  }

  static partnershipRequest = (data, config) => {
    toast.dismiss(toastID);
    toastID = toast(<PartnershipRequestToast data={data} />, {
      ...toastDefaultConfig,
      ...config
    })
  }
}

export default Notify;

const InfoToaster = ({ text }) => (
  <div className="toast_info">
    <div className="toast_info__inner">
      <div className={classnames('toast_info__text')}>
        {text || ''}
      </div>
    </div>
  </div>
);

const SuccessToaster = ({ text }) => (
   <div className="toast_success">
     <div className="toast_success__inner row">
       <div className="toast_success__icon">
         <svg width="20" height="14" viewBox="0 0 20 14" fill="none" xmlns="http://www.w3.org/2000/svg">
           <path d="M7 11.5858L1.70711 6.29289C1.31658 5.90237 0.683418 5.90237 0.292893 6.29289C-0.0976311 6.68342 -0.0976311 7.31658 0.292893 7.70711L6.29289 13.7071C6.68342 14.0976 7.31658 14.0976 7.70711 13.7071L19.7071 1.70711C20.0976 1.31658 20.0976 0.683418 19.7071 0.292893C19.3166 -0.0976311 18.6834 -0.0976311 18.2929 0.292893L7 11.5858Z" fill="white"/>
         </svg>
       </div>

       <div className="toast_success__text f-15">
         {text || ''}
       </div>
     </div>
     <CloseButton className="toast_success__close" />
   </div>
);
