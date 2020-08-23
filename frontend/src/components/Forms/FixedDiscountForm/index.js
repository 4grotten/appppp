import React from 'react';
import * as classnames from 'classnames';
import {DISCOUNT_TYPES} from '../../../common/constants';
import {RemoveIcon} from '../../UI/Icons';
import {ONLY_DIGITS} from '../../../common/helpers';
import './index.scss';

class FixedDiscountForm extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      id: props.card.id || new Date().toISOString(),
      type: props.card.type || DISCOUNT_TYPES.fixed,
      percent: props.card.percent || 5
    }
  }

  setFieldValue = async (field, value) => {
    if (field === 'percent') {
      const num = parseInt(value);
      if (!value.match(ONLY_DIGITS) ||  num > 100 || num === 0) {
        return;
      }
    }

    await this.setState({...this.state, [field]: value})
    this.props.onChange({ ...this.props.card, ...this.state, changed: true });
  }

  render() {
    const { onRemove, isEditable, error } = this.props;

    return (
      <div className={classnames("fixed-discount-form f-15", error && "fixed-discount-form__error")}>
        <div className="fixed-discount-form__inner">
          <div className={classnames(
            "fixed-discount-form__row",
            "fixed-discount-form__discount",
            error && error.percent && "fixed-discount-form__discount-error"
          )}>
            <label htmlFor={`percent${this.state.id}`} >{(error && error.percent) || 'Процент скидки'}</label>
            <div>
              <input
                name={`percent${this.state.id}`}
                id={`percent${this.state.id}`}
                type="text"
                value={this.state.percent}
                onChange={(e) => this.setFieldValue('percent', e.target.value)}
              />
              <span>%</span>
            </div>
          </div>
        </div>

        <button className={classnames("fixed-discount-form__delete", isEditable === false && "fixed-discount-form__delete-not")} onClick={onRemove}>
          <RemoveIcon />
        </button>
      </div>
    )
  }
}

export default FixedDiscountForm;