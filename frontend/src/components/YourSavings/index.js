import React, {Component} from 'react';
import {connect} from 'react-redux';
import {getCurrencies} from '../../store/actions/commonActions';
import {getDataFromLocalStorage, saveDataToLocalStorage} from '../../store/localStorage';
import {getStatisticSummary} from '../../store/actions/statisticActions';
import './index.scss';

class YourSavings extends Component {
  componentDidMount() {
    this.props.getCurrencies();
  }

  onChange = (e) => {
    const current = getDataFromLocalStorage('myCurrency');
    if (e.target.value !== current) {
      saveDataToLocalStorage('myCurrency', e.target.value);
      this.props.getStatisticSummary();
    }
  }

  render() {
    const { savings, myCurrency } = this.props;
    const { data } = this.props.currency;
    const list = (data && data.map(country => country.currency.code)) || []
    let currencies = [...new Set(list)];

    return (
      <div className="your-savings">
        <div className="your-savings__label f-15">Ваша экономия</div>
        <div className="row">
          <div className="your-savings__value f-600 f-16">{savings || 0}</div>
          <div className="dfc">
            <select className="your-savings__select f-600 f-16" value={myCurrency} onChange={this.onChange}>
              {!data &&  <option value={myCurrency} >{myCurrency}</option>}
              {currencies.map(currency => (
                <option key={currency} value={currency}>
                  {currency}
                </option>
              ))}
            </select>
            <svg width="13" height="8" viewBox="0 0 13 8" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M10.8803 0.705324C11.2701 0.315536 11.9042 0.317662 12.2922 0.705627L12.38 0.793473C12.77 1.18343 12.7726 1.81306 12.3781 2.20754L7.29407 7.29156C6.90306 7.68257 6.27258 7.68604 5.8781 7.29156L0.794074 2.20754C0.403064 1.81653 0.4042 1.18144 0.792165 0.793473L0.88001 0.705627C1.26997 0.315672 1.89886 0.312323 2.29186 0.705324L6.58609 4.99955L10.8803 0.705324Z" fill="#4285F4"/>
            </svg>
          </div>
        </div>
      </div>
    );
  }
}

const mapStateToProps = state => ({
  currency: state.commonStore.currency
})

const mapDispatchToProps = dispatch => ({
  getCurrencies: () => dispatch(getCurrencies()),
  getStatisticSummary: () => dispatch(getStatisticSummary()),
})

export default connect(mapStateToProps, mapDispatchToProps)(YourSavings);