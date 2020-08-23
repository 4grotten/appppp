import React from 'react';
import Modal from 'react-modal';
import {mobileMenuStyles} from '../../assets/styles/modal';
import {CloseButton} from '../UI/Icons';
import './index.scss';

const MobileMenu = ({ isOpen, onRequestClose, onClose, style = mobileMenuStyles, contentLabel, children, ...other }) => {
  React.useEffect(() => {
    if (isOpen) { document.body.style.overflow = 'hidden' }
    else { document.body.style.overflow = 'unset' }
    return () => document.body.style.overflow = 'unset'
  }, [ isOpen ]);

  return (
    <Modal
      isOpen={isOpen}
      onRequestClose={onRequestClose}
      contentLabel={contentLabel || "Example Modal"}
      style={style}
      appElement={document.getElementById("root")}
      {...other}
    >
      <div className="container">
        <div className="mobile-menu__top">
          <h5 className="mobile-menu__title f-20 f-800 tl">{contentLabel || 'Настройки'}</h5>
          <CloseButton className="mobile-menu__close-btn" onClick={onClose ? onClose : onRequestClose} />
        </div>
        <div className="mobile-menu__content">
          {children}
        </div>
      </div>
    </Modal>
  )
};

export default MobileMenu;