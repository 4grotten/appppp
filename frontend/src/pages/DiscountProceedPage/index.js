import React from 'react';
import {connect} from 'react-redux';
import DiscountProceedForm from '../../components/Forms/DiscountProceedForm';
import {completeDscTransaction, preprocessDiscount} from '../../store/actions/discountActions';

class DiscountProceedPage extends React.Component {
  componentDidMount() {
    if (!this.props.preOrganization) {
      this.props.history.push('/profile');
    }
  }

  onSubmit = async (values, { setSubmitting }) => {
    const { history,  preOrganization } = this.props;
    const {
      data,
      amount,
      manualPercent,
      percent,
      sourceCard
    } = values

    const payload = {
      transaction_id: data && data.transaction_id,
      original_amount: Number(amount),
      discount_percent: 0,
      source_card: null
    }

    if (!!parseInt(manualPercent)) {
      payload.discount_percent = Number(manualPercent);
    } else if (!!Number(percent) && sourceCard) {
      payload.source_card = Number(sourceCard);
      payload.discount_percent = Number(percent);
    }

    const res = await this.props.completeDscTransaction(payload);
    if (res && res.success) {
      return history.push(`/organizations/${preOrganization.id}`)
    } else {
      setSubmitting(false);
    }
  }

  render() {
    const { preprocessDiscount, preOrganization, history } = this.props;
    if (!preOrganization) { return null; }

    return (
      <div className="discount-proceed-page">
        <DiscountProceedForm
          preprocessDiscount={preprocessDiscount}
          preOrganization={preOrganization}
          onSubmit={this.onSubmit}
          history={history}
        />
      </div>
    );
  }
}

const mapStateToProps = state => ({
  preOrganization: state.discountStore.preOrganization,
});

const mapDispatchToProps = dispatch => ({
  preprocessDiscount: userID => dispatch(preprocessDiscount(userID)),
  completeDscTransaction: payload => dispatch(completeDscTransaction(payload)),
});

export default connect(mapStateToProps, mapDispatchToProps)(DiscountProceedPage);