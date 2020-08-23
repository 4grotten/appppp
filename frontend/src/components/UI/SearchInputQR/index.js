import React from 'react';
import {BackArrow, SearchIcon} from '../Icons';
import './index.scss';

const SearchInputQR = ({ value, onChange, placeholder, onSubmit, name }) => {
  return (
    <div className="search-input-qr">
      <SearchIcon className="search-input-qr__search" />
      <input
        name={name}
        value={value}
        onChange={onChange}
        type="text"
        className="search-input-qr__input f-17"
        placeholder={placeholder || "Поиск по ID"}
      />
      {value && (
        <button type="button" className="search-input-qr__submit" onClick={onSubmit} >
          <BackArrow />
        </button>
      )}
    </div>
  );
};

export default SearchInputQR;