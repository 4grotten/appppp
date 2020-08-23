import * as React from 'react';
import ReactCodeInput from 'react-verification-code-input';
import './index.scss';

export const VerificationCodeInput = ({ onChange, onComplete, values }) => (
  <ReactCodeInput
    type="number"
    fields={6}
    onChange={onChange}
    onComplete={onComplete}
    autoFocus={true}
    loading={false}
    values={values}
    fieldWidth={44}
    className="verification-code"
  />
)