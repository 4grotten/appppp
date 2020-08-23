import React from 'react';
import './index.scss';

const CurrencyCard = ({ country, onClick }) => (
  <div className="currency-card row" onClick={onClick}>
    <div className="currency-card__left dfc">
      <div className="currency-card__image"><img src={country.flag} alt={country.name} /></div>
      <p className="f-15 country-card__name">{country.name}</p>
    </div>
    <div className="f-15 currency-card__code">
      {country.currency.code}
    </div>
  </div>
);

export default CurrencyCard;