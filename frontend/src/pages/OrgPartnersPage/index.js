import React from 'react';
import MobileSearchHeader from '../../components/MobileSearchHeader';
import {connect} from 'react-redux';
import {
  createPartnership,
  getOrgPartnerships,
  rejectPartnership,
  setPartnershipPermissions
} from '../../store/actions/partnerActions';
import Preloader from '../../components/Preloader';
import EmptyBox from '../../components/EmptyBox';
import InfiniteScroll from 'react-infinite-scroll-component';
import {CloseIcon} from '../../components/UI/Icons';
import OrgAvatar from '../../components/UI/OrgAvatar';
import {QRCode} from 'react-qr-svg';
import {QR_ORG_PREFIX} from '../../common/constants';
import {getOrganizationDetail} from '../../store/actions/organizationActions';
import ScanView from '../../containers/ScanView';
import Button from '../../components/UI/Button';
import PartnershipCard from '../../components/Cards/PartnershipCard';
import './index.scss';

class OrgPartnersPage extends React.Component {
  constructor(props) {
    super(props);
    this.organization = props.match.params.id;
    this.state = {
      step: 0,
      page: 1,
      limit: 10
    }
  }

  componentDidMount() {
    this.props.getOrganizationDetail(this.organization);
    this.props.getOrgPartnerships(this.organization, this.state);
  }

  onScan = async orgID => {
    if (this.props.orgDetail.data && orgID && orgID.includes(QR_ORG_PREFIX)) {
      const res = await this.props.createPartnership({
        requested_by: this.props.orgDetail.data.id,
        accepted_by: orgID.replace(QR_ORG_PREFIX, '')
      });
      if (res && res.success) {
        this.setState({ ...this.state, step: 0 });
        // this.props.getOrgPartnerships(this.organization, this.state);
      }
    }
  }

  getNext = totalPages => {
    if (this.state.page < totalPages) {
      const nextPage = this.state.page + 1
      this.props.getOrgPartnerships(this.organization, {
        ...this.state,
        page: nextPage,
      }, true);

      return this.setState({ ...this.state, hasMore: true, page: nextPage })
    }
    this.setState({ ...this.state, hasMore: false });
  }

  render() {
    const { orgPartnerships, orgDetail, setPartnershipPermissions, rejectPartnership, history } = this.props;
    const { data, loading } = orgPartnerships;
    const { page, step } = this.state;

    return (
      <div className="org-partners-page">
        {step === 0 && (
          <React.Fragment>
            <MobileSearchHeader
              title="Партнеры"
              onBack={() => history.push(`/organizations/${this.organization}`)}
              onSearchChange={() => null}
            />

            <div className="org-partners-page__content">
              <div className="container">
                <p className="f-20 f-800">{(data && data.total_count) || 0} партнера</p>
                <div className="org-partners-page__list">
                  {(page === 1 && loading)
                    ?  <Preloader />
                    : (!data || (data && !data.total_count))
                      ? <EmptyBox title="Нет партнеров" description={!!this.state.search && 'Поиск не дал результатов'} />
                      : (
                        <InfiniteScroll
                          dataLength={Number(data.list.length) || 0}
                          next={() => this.getNext(data.total_pages)}
                          hasMore={this.state.hasMore}
                          loader={null}
                        >
                          {data.list.map(partnership => {
                            return (
                              <PartnershipCard
                                key={partnership.id}
                                partner={partnership.partner}
                                onAcceptPartnership={() => setPartnershipPermissions(partnership.id, {}).then(res => {
                                  res && res.success && history.push(`/organizations/${this.organization}/partners/${partnership.id}`);
                                })}
                                onRejectPartnership={() => rejectPartnership(partnership.id)}
                                isAccepted={partnership.is_accepted}
                                isIncoming={partnership.is_incoming}
                                to={partnership.is_accepted && `/organizations/${this.organization}/partners/${partnership.id}`}
                                className="org-partners-page__item"
                              />
                             )
                          })}
                        </InfiniteScroll>
                      )}
                </div>
                <div className="org-partners-page__tools">
                  <Button
                    label="Сканировать QR"
                    type="button"
                    onClick={() => this.setState({ ...this.state, step: 2 })}
                  />

                  <Button
                    label="QR организации"
                    type="button"
                    onClick={() => this.setState({ ...this.state, step: 1 })}
                  />
                </div>
              </div>
            </div>
          </React.Fragment>
        )}

        {step === 1 && orgDetail.data && (
          <div className="org-partners-page__qr">
            <div className="container">
            <div className="org-partners-page__qr-header row">
              <button
                onClick={() => this.setState({ ...this.state, step: 0 })}
                style={{ height: '24px'}}
              >
                <CloseIcon />
              </button>
              {/*<ShareIcon />*/}
            </div>
              <div className="org-partners-page__qr-organization">
                <OrgAvatar
                  src={orgDetail.data.image && orgDetail.data.image.medium}
                  alt={orgDetail.data.title}
                  size={72}
                  className="org-partners-page__qr-organization-avatar"
                />
                <h1 className="org-partners-page__qr-organization-title f-20 f-800">{orgDetail.data.title}</h1>
              </div>

              <div className="org-partners-page__qr-code">
                <QRCode
                  bgColor="#FFFFFF"
                  fgColor="#4285F4"
                  level="H"
                  style={{ width: 250 }}
                  value={`${QR_ORG_PREFIX}${orgDetail.data.id}`}
                />
              </div>

              <p className="org-partners-page__qr-id f-20 f-600">ID {orgDetail.data.id}</p>
            </div>
          </div>
        )}

        {step === 2 && orgDetail.data && (
          <ScanView
            onError={() => null}
            onScan={this.onScan}
            onInputSubmit={this.onScan}
          >
            <div  className="org-partners-page__scan-header row">
              <button
                type="button"
                onClick={() => this.setState({ ...this.state, step: 0 })}
                className="org-partners-page__scan-back"
              >
                <CloseIcon />
              </button>

              <OrgAvatar
                src={orgDetail.data.image && orgDetail.data.image.medium}
                alt={orgDetail.data.title}
                size={44}
              />
            </div>
          </ScanView>
        )}
      </div>
    );
  }
}

const mapStateToProps = state => ({
  orgDetail: state.organizationStore.orgDetail,
  orgPartnerships: state.partnerStore.orgPartnerships,
})

const mapDispatchToProps = dispatch => ({
  getOrgPartnerships: (orgID, param, isNext) => dispatch(getOrgPartnerships(orgID, param, isNext)),
  getOrganizationDetail: (orgID) => dispatch(getOrganizationDetail(orgID)),
  createPartnership: payload => dispatch(createPartnership(payload)),
  rejectPartnership: id => dispatch(rejectPartnership(id)),
  setPartnershipPermissions: (id, payload) => dispatch(setPartnershipPermissions(id, payload)),
})

export default connect(mapStateToProps, mapDispatchToProps)(OrgPartnersPage);