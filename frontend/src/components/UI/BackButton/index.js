import * as React from 'react'
import * as classnames from 'classnames'
import './index.scss'

export const BackButton = ({onClick, className}) => (
  <button
    type="button"
    onClick={onClick}
    className={classnames("back-button", className)}
  />
)