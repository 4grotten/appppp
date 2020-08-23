import React, {Component} from 'react';
import MobileTopHeader from '../../components/MobileTopHeader';
import ReceiptDetail from '../../components/ReceiptDetail';
import {connect} from 'react-redux';
import {getOrganizationTitle, getReceiptDetail} from '../../store/actions/statisticActions';
import Preloader from '../../components/Preloader';
import qs from 'qs';
import './index.scss';

class ReceiptDetailPage extends Component {
  componentDidMount() {
    const {match, location, getReceiptDetail, getOrganizationTitle}  = this.props;
    const { id } = match.params;
    const { org } = qs.parse(location.search.replace('?', ''));
    id && getReceiptDetail(id);
    org && getOrganizationTitle(org).then(res => {
      if (res && res.success) {
        this.setState({ title: res.title })
      }
    });
  }

  state = { title: '' };

  render() {
    const { receiptDetail, history } = this.props;
    const { data, loading } = receiptDetail;

    return (
      <div className="receipt-detail-page">
        <MobileTopHeader
          onBack={() => history.goBack()}
          title={this.state.title}
        />
        <div className="container">
          {!data && loading && <Preloader />}
          {data && !loading && (
            <ReceiptDetail
              receipt={data}
              showOrganization
              className="receipt-detail-page__receipt"
            />
          )}
        </div>
      </div>
    );
  }
}

const mapStateToProps = state => ({
  receiptDetail: state.statisticStore.receiptDetail,
})

const mapDispatchToProps = dispatch => ({
  getReceiptDetail: id => dispatch(getReceiptDetail(id)),
  getOrganizationTitle: id => dispatch(getOrganizationTitle(id)),
})

export default connect(mapStateToProps, mapDispatchToProps)(ReceiptDetailPage);