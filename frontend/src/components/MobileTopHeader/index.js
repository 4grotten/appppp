import React from 'react';
import * as classnames from 'classnames';
import {BackArrow, MenuDots} from '../UI/Icons';
import PropTypes from 'prop-types';
import './index.scss';

const MobileTopHeader = props => {
  const { title, onBack, onNext, onSubmit, submitLabel, nextLabel, onMenu, disabled, renderLeft, renderRight, className } = props;

  return (
    <div className={classnames("mobile-top-header__wrap", className)}>
      <div className="container">
        <div className="mobile-top-header">
          <div className="mobile-top-header__left">
            {renderLeft && renderLeft()}
            {onBack && <button type="button" onClick={onBack} className="mobile-top-header__back" ><BackArrow /></button>}
          </div>
          <h1 className="mobile-top-header__title tl f-16 f-600">{title}</h1>
          <div className="mobile-top-header__right">
            {renderRight && renderRight()}
            {onSubmit && <button type="submit" onSubmit={onSubmit} disabled={disabled} className={classnames("mobile-top-header__submit f-14 f-600", submitLabel === 'Сохранение' && "mobile-top-header__submit-loading")}>{submitLabel}</button>}
            {onNext && <button type="button" onClick={onNext} className="mobile-top-header__next f-14 f-600">{nextLabel}</button>}
            {onMenu && <button type="button" onClick={onMenu} className="mobile-top-header__menu f-14"><MenuDots /></button>}
          </div>
        </div>
      </div>
    </div>
  );
};

MobileTopHeader.defaultProps = {
  title: '',
  submitLabel: 'Сохранить',
  nextLabel: 'Далее',
}

MobileTopHeader.propTypes = {
  title: PropTypes.string,
  onBack: PropTypes.func,
  onNext: PropTypes.func,
  onSubmit: PropTypes.func,
  submitLabel: PropTypes.string,
  nextLabel: PropTypes.string,
  onMenu: PropTypes.func,
  renderLeft: PropTypes.func,
  renderRight: PropTypes.func,
  disabled: PropTypes.bool,
  className: PropTypes.string,
};

export default MobileTopHeader;