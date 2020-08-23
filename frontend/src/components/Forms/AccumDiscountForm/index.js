import React from 'react';
import * as classnames from 'classnames';
import {DISCOUNT_TYPES} from '../../../common/constants';
import {RemoveIcon} from '../../UI/Icons';
import {ONLY_DIGITS} from '../../../common/helpers';
import './index.scss';

class AccumDiscountForm extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      id: props.card.id || new Date().toISOString(),
      type: props.card.type || DISCOUNT_TYPES.cumulative,
      percent: props.card.percent || '5',
      currency: props.card.currency || 'KGS',
      limit: props.card.limit || '10000',
    }
  }

  setFieldValue = async (field, value) => {
    if (this.props.isEditable === false) { return; }

    if (field === 'percent') {
      const num = parseInt(value);
      if (!value.match(ONLY_DIGITS) ||  num > 100 || num === 0) {
        return;
      }
    }

    if (field === 'limit') {
      const num = parseInt(value);
      if (!value.match(ONLY_DIGITS) || num > 10000000 || num === 0 )
        return;
    }

    await this.setState({...this.state, [field]: value})
    this.props.onChange({ ...this.props.card, ...this.state, changed: true });
  }

  render() {
    const { onRemove, isEditable, error } = this.props;

    return (
      <div className={classnames("accum-discount-form f-15", error && "accum-discount-form__error")}>
        <div className="accum-discount-form__inner">
          <div className={classnames("accum-discount-form__row accum-discount-form__discount", error && error.percent && "accum-discount-form__row accum-discount-form__discount-error")}>
            <label htmlFor={`percent${this.state.id}`} >{(error && error.percent) || 'Процент скидки'}</label>
            <div>
              <input
                name={`percent${this.state.id}`}
                id={`percent${this.state.id}`}
                type="text"
                value={this.state.percent}
                disabled={isEditable === false}
                onChange={(e) => this.setFieldValue('percent', e.target.value)}
              />
              <span>%</span>
            </div>
          </div>

          <div className="accum-discount-form__row accum-discount-form__currency">
            <label htmlFor="" className="">Валюта</label>
            <input
              value={this.state.currency}
              onChange={() => null}
              disabled
            />
          </div>

          <div className={classnames("accum-discount-form__row accum-discount-form__limit", error && error.limit && "accum-discount-form__limit-error")}>
            <label htmlFor="">{(error && error.limit) || 'Лимит накопления'}</label>
            <input
              type="text"
              value={this.state.limit}
              disabled={isEditable === false}
              onChange={(e) => this.setFieldValue('limit', e.target.value)}
            />
          </div>
        </div>

        <button type="button" className={classnames("accum-discount-form__delete", isEditable === false && "accum-discount-form__delete-not") } onClick={onRemove}>
          <RemoveIcon />
        </button>
      </div>
    )
  }
}

export default AccumDiscountForm;