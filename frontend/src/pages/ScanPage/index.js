import React from 'react';
import ScanView from '../../containers/ScanView';
import {BackArrow} from '../../components/UI/Icons';

const ScanPage = ({ history }) => {
  return (
    <ScanView
      onScan={() => null}
      onError={() => null}
    >
      <button
        type="button"
        onClick={() => history.push('/profile')}
        className="discount-proceed-form__rounded-btn"
      >
        <BackArrow />
      </button>
    </ScanView>
    );
};

export default ScanPage;