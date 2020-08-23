import React from 'react';
import * as classnames from 'classnames';
import {BackArrow, SearchIcon} from '../UI/Icons';
import SearchField from '../UI/SearchField';
import './index.scss';

const MobileSearchHeader = ({ title = '', renderHeader, searchName, searchValue, onSearchChange, onSearchSubmit, searchPlaceholder, onSearchCancel, onBack, defaultState }) => {
  const [showSearch, setShow] = React.useState(!!defaultState);

  return (
    <div className="mobile-search-header__wrap">
      <div className="container">
        <div className="mobile-search-header row">
          <div className={classnames(
            "mobile-search-header__main", "row",
            !showSearch && "mobile-search-header__main-active")}
          >
            {onBack && <BackArrow className="mobile-search-header__main-back" onClick={onBack} />}
            {renderHeader ? renderHeader() : <h5 className="f-16 f-600 tl">{title}</h5>}
            {onSearchChange && (
              <button type="button" onClick={() => setShow(!showSearch)} className="mobile-search-header__main-search">
                <SearchIcon />
              </button>
            )}
          </div>

          <div className={classnames(
            "mobile-search-header__search", "row",
            showSearch && "mobile-search-header__search-active")}
          >
            <SearchField
              name={searchName}
              value={searchValue}
              onChange={onSearchChange}
              onSubmit={onSearchSubmit}
              placeholder={searchPlaceholder}
            />
            <button type="button" onClick={() => {
              onSearchCancel && onSearchCancel();
              setShow(!showSearch)
            }} className="mobile-search-header__search-button">
              Отметить
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MobileSearchHeader;