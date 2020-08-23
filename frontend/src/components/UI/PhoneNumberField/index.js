import * as React from 'react';
import * as classnames from 'classnames';
import PhoneInput from 'react-phone-input-2'
import ru from 'react-phone-input-2/lang/ru.json'
import 'react-phone-input-2/lib/style.css'
import './index.scss';

const PhoneInputField = ({className, value, name, label, countryCode, onChange}) => (
  <PhoneInput
    containerClass={classnames("phone-input-field", className)}
    country={(countryCode && countryCode.toLowerCase()) || 'kg'}
    localization={ru}
    placeholder={label}
    value={value}
    inputClass="phone__input"
    buttonClass="phone__button"
    inputProps={{ name }}
    preferredCountries={['ru','kg','kz', 'am', 'uz', 'by']}
    onChange={phone => onChange(phone)}
  />
)

export default PhoneInputField;