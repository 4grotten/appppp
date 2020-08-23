import React from 'react';
import MobileTopHeader from '../../components/MobileTopHeader';
import {connect} from 'react-redux';
import {getCurrencies} from '../../store/actions/commonActions';
import CurrencyCard from '../../components/Cards/CurrencyCard';
import Preloader from '../../components/Preloader';
import './index.scss';

class CurrencyView extends React.Component {
  componentDidMount() {
    this.props.getCurrencies();
  }

  render() {
    const { data, loading } = this.props.currency;
    const { onBack, onChange } = this.props;

    return (
      <div className="currency-view">
        <MobileTopHeader
          onBack={onBack}
          title="Выбрать валюту"
        />
        <div className="container">
          {!data && loading && <Preloader />}
          {data && data.map(country => <CurrencyCard key={country.code} country={country} onClick={() => onChange(country)} />)}
        </div>
      </div>
    )
  }
}

const mapStateToProps = state => ({
  currency: state.commonStore.currency
});

const mapDispatchToProps = dispatch => ({
  getCurrencies: () => dispatch(getCurrencies())
});

export default connect(mapStateToProps, mapDispatchToProps)(CurrencyView);