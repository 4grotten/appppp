import React, {Component} from 'react';
import MobileTopHeader from '../../components/MobileTopHeader';
import ReceiptDetail from '../../components/ReceiptDetail';
import {connect} from 'react-redux';
import Preloader from '../../components/Preloader';
import {getOrgReceiptDetail, removeReceipt} from '../../store/actions/organizationActions';
import Avatar from '../../components/UI/Avatar';
import './index.scss';

class OrgReceiptDetailPage extends Component {
  constructor(props) {
    super(props);
    this.receiptID = props.match.params.receiptID;
    this.organizationID = props.match.params.id;
    this.state = { isRemoving: false }
  }

  componentDidMount() {
    this.receiptID ? this.props.getOrgReceiptDetail(this.receiptID) : this.organizationID
      ? this.props.history.push(`/organizations/${this.organizationID}`)
      : this.props.history.push(`/profile`)
  }

  removeReceipt = async () => {
    const id = this.props.orgReceiptDetail.data && this.props.orgReceiptDetail.data.id;
    const confirmed = window.confirm('Вы уверены, что хотите удалить данный чек ?');

    if (id && confirmed) {
      await this.setState({ isRemoving: true });
      const res = await this.props.removeReceipt(id);
      if (res && res.success) {
        return this.props.history.push(`/organizations/${this.organizationID}/receipts`)
      }
      this.setState({ isRemoving: false });
    }
  }

  render() {
    const { orgReceiptDetail, history } = this.props;
    const { data, loading } = orgReceiptDetail;

    return (
      <div className="org-receipt-detail-page">
        <MobileTopHeader
          onBack={() => history.goBack()}
          title={`Чек ${this.receiptID}`}
        />
        <div className="container">
          {loading ? <Preloader /> : data && (
            <ReceiptDetail
              receipt={data}
              viewProceederReceipts={true}
              organizationID={this.organizationID}
              onRemove={this.removeReceipt}
              isRemoving={this.state.isRemoving}
              className="org-receipt-detail-page__receipt"
            >
              {data.client && (
                <div className="org-receipt-detail-page__client">
                  <Avatar
                    src={data.client.avatar && data.client.avatar.medium}
                    alt={data.client.full_name}
                    size={48}
                    className="org-receipt-detail-page__client-avatar"
                  />

                  <div className="org-receipt-detail-page__client-right">
                    <p className="f-14">Клиент</p>
                    <h2 className="f-17">{data.client.full_name}</h2>
                  </div>
                </div>
              )}
            </ReceiptDetail>
          )}
        </div>
      </div>
    );
  }
}

const mapStateToProps = state => ({
  orgDetail: state.organizationStore.orgDetail,
  orgReceiptDetail: state.organizationStore.orgReceiptDetail,
})

const mapDispatchToProps = dispatch => ({
  getOrgReceiptDetail: id => dispatch(getOrgReceiptDetail(id)),
  removeReceipt: id => dispatch(removeReceipt(id)),
})

export default connect(mapStateToProps, mapDispatchToProps)(OrgReceiptDetailPage);