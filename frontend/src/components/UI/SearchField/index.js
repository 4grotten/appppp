import React from 'react';
import {SearchIcon} from '../Icons';
import './index.scss'

const SearchField = ({ name, value, placeholder, onSubmit, onChange }) => (
  <form className="search-field" onSubmit={onSubmit ? onSubmit : e => e.preventDefault()}>
    <SearchIcon />
    <input
      type="text"
      name={name || 'search'}
      value={value}
      onChange={onChange}
      placeholder={placeholder || 'Поиск'}
      className="search-field__input"
    />
  </form>
);

export default SearchField;