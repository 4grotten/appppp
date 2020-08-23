import React, {Component} from 'react';
import MobileTopHeader from '../../components/MobileTopHeader';
import {Formik} from 'formik';
import PartnerCard from '../../components/Cards/PartnerCard';
import RowToggle from '../../components/UI/RowToggle';
import {connect} from 'react-redux';
import {getPartnershipDetail, setPartnershipPermissions} from '../../store/actions/partnerActions';
import Notify from '../../components/Notification';
import './index.scss';

class PartnershipDetailPage extends Component {
  constructor(props) {
    super(props);
    this.partnerID = props.match.params.partnerID;
  }

  componentDidMount() {
    this.props.getPartnershipDetail(this.partnerID);
  }

  onSubmit = (values) => {
    this.props.setPartnershipPermissions(this.partnerID, values).then(res => {
      res && res.success && Notify.success({ text: 'Права успешно обновлены' });
    })
  }

  render() {
    const { partnershipDetail, history } = this.props;
    const { data } = partnershipDetail;
    if (!data) { return null; }
    const { requested_by, can_check_attendance, can_see_stats, can_edit_organization } = data;
    return (
      <Formik
        onSubmit={(values, formikBag) => this.onSubmit(values, formikBag)}
        initialValues={{
          can_check_attendance,
          can_see_stats,
          can_edit_organization,
        }}
      >
        {({ values, handleChange, handleSubmit }) => (
          <form onSubmit={handleSubmit} className="partnership-detail-page">
            <MobileTopHeader
              onBack={() => history.goBack()}
              title="Ваши партнеры"
              onSubmit={handleSubmit}
            />
            <div className="content">
              <div className="container">
                <PartnerCard
                  partner={requested_by}
                  to={"#"}
                  className="partnership-detail-page__card"
                />
                <h4 className="partnership-detail-page__title f-14 f-600">Управление</h4>
                <RowToggle
                  name="can_check_attendance"
                  label="Сканировать пропуска"
                  checked={values.can_check_attendance}
                  onChange={handleChange}
                />
                <RowToggle
                  name="can_see_stats"
                  label="Статистика продаж/скидок"
                  checked={values.can_see_stats}
                  onChange={handleChange}
                />
                <RowToggle
                  name="can_edit_organization"
                  label="Редактировать организацию"
                  checked={values.can_edit_organization}
                  onChange={handleChange}
                />
              </div>
            </div>
          </form>
        )}
      </Formik>
    );
  }
}

const mapStateToProps = state => ({
  partnershipDetail: state.partnerStore.partnershipDetail,
})

const mapDispatchToProps = dispatch => ({
  getPartnershipDetail: id => dispatch(getPartnershipDetail(id)),
  setPartnershipPermissions: (id, payload) => dispatch(setPartnershipPermissions(id, payload)),
})

export default connect(mapStateToProps, mapDispatchToProps)(PartnershipDetailPage);