import React from 'react';
import ReactDOM from 'react-dom';

const Portal = ({ children, elementID = 'control' }) => {
  return ReactDOM.createPortal(
    children,
    document.getElementById(elementID)
  );
};

export default Portal;