import * as React from 'react';
import './index.scss';

const SearchInput = ({value, onchange, name, ...other}) => (
  <div className="search-input">
    <label className="search-input__label" htmlFor="name" />
    <input
      className="search-input__input"
      type="text"
      name={name}
      id={name}
      value={value}
      onChange={onchange}
      {...other}
    />
  </div>
)

export default SearchInput;