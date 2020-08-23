import React from 'react';
import QrReader from 'react-qr-reader'
import SearchInputQR from '../../components/UI/SearchInputQR';
import './index.scss';

const ScanView = ({ onError, onScan, children, onInputSubmit, inputPlaceholder, delay = 300 }) => {
  const [text, setText] = React.useState('');
  const onChange = e => {
    setText(e.target.value);
  };
  return (
    <div className="scan-view">
      <div className="scan-view__top">
        <div className="container">
        {children}
        </div>
      </div>

      <div className="scan-view__reader-container">
        <div className="container">
          <QrReader
            delay={delay}
            onError={onError}
            onScan={onScan}
            facingMode="environment"
            className="scan-view__reader"
          />
        </div>
      </div>

      {onInputSubmit && (
        <div className="scan-view__bottom">
          <div className="container">
            <SearchInputQR
              onChange={onChange}
              name="id"
              placeholder={inputPlaceholder}
              value={text}
              onSubmit={() => onInputSubmit(text)}
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default ScanView;