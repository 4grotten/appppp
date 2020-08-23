import * as React from "react";
import SearchInput from "../../components/UI/SearchInput";

import { getCountries, getCountryCallingCode } from 'react-phone-number-input/input'
import en from 'react-phone-number-input/locale/en.json'

const CountryDialSelect = () => {
  return (
    <div style={{marginTop: '50px'}}>
      <h2>Выбрать страну</h2>
      <SearchInput
        value={''}
        name="search"
        onchange={() => null}
        placeholder="Поиск"
      />
      <br/>
      <br/>
      <br/>

      <ul>
        {getCountries().map((country) => {
          console.log('Country', country)

          const countryCode = getCountryCallingCode(country);
          console.log('Dial', countryCode)
          const countryName = en[country];
          return (
            <li key={country} onClick={() => console.log(country) }>
              <div>
                <img
                  alt={countryName}
                  src={`http://catamphetamine.gitlab.io/country-flag-icons/3x2/${country}.svg`}
                />
                <span>{countryName}</span>
              </div>
              <span>{countryCode}</span>
            </li>
          )
        })}


      </ul>
    </div>
  )
}

export default CountryDialSelect;