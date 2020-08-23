import React from 'react';
import {connect} from 'react-redux';
import OrganizationEditDiscountsForm from '../../components/Forms/Organization/OrganizationEditDiscountsForm';
import {
  bulkDeleteOrgDiscounts,
  bulkUpdateOrgDiscounts,
  createOrganizationDiscount
} from '../../store/actions/organizationActions';

class OrgEditDiscountPage extends React.Component {
  componentDidMount() {
    const organization = this.props.orgDetail.data;
    const { id } = this.props.match.params;

    if (!organization) {
      return this.props.history.push(`/organizations/${id}`);
    }
  }

  onSubmit = async (values, { setSubmitting }) => {
    const { id } = this.props.match.params;
    const organization = this.props.orgDetail.data;

    if (id === (organization && JSON.stringify(organization.id))) {
      const { createDiscounts, updateDiscounts, deleteDiscounts } = this.props;
      const {
        fixedDiscounts,
        accDiscounts
      } = values;

      const createPending = [];
      const deletePending = [];
      const updatePending = {
        fixed: [],
        cumulative: []
      };

      const prevCardsCount = [];
      organization && organization.discounts.cumulative.map(card => prevCardsCount.push(card.id));
      organization && organization.discounts.fixed.map(card => prevCardsCount.push(card.id));

      const existingCardsCount = [];

      fixedDiscounts.map(card => {
        existingCardsCount.push(card.id);

        if (!Object.keys(card).includes('is_editable')) {
          return createPending.push({
            type: card.type,
            percent: card.percent,
            limit: null,
            currency: organization.currency
          })
        }

        if (card.is_editable && card.changed) {
          updatePending.fixed.push({
            id: card.id,
            percent: card.percent,
            limit: null
          })
        }
      });

      accDiscounts.map(card => {
        existingCardsCount.push(card.id);

        if (!Object.keys(card).includes('is_editable')) {
          return createPending.push({
            type: card.type,
            percent: card.percent,
            limit: card.limit,
            currency: organization.currency
          })
        }

        if (card.is_editable && card.changed) {
          updatePending.cumulative.push({
            id: card.id,
            percent: card.percent,
            limit: card.limit
          })
        }
      });

      let currentCardListID = existingCardsCount.filter(id => !isNaN(id));
      prevCardsCount.map(id => !currentCardListID.includes(id) && deletePending.push(id));

      if (!!deletePending.length) {
        const res = await deleteDiscounts({
          organization: organization.id,
          cards: deletePending
        })

        if (res && !res.success) {
          return setSubmitting(false);
        }
      }

      if (!!updatePending.fixed.length || !!updatePending.cumulative.length) {
        await updateDiscounts({
          organization: organization.id,
          cards: [...updatePending.fixed, ...updatePending.cumulative]
        })
      }

      if (!!createPending.length) {
        await createDiscounts({
          organization: organization.id,
          cards: createPending
        })
      }

      this.props.history.push(`/organizations/${organization.id}`);
    }
  }

  render() {
    const { history, orgDetail, match } = this.props;
    const { data } = orgDetail;

    if (!data) {
      return null;
    }

    return (
      <div className="org-edit-discount-page">
        <OrganizationEditDiscountsForm
          id={match.params.id}
          data={data}
          history={history}
          onSubmit={this.onSubmit}
        />
      </div>
    );
  }
}

const mapStateToProps = state => ({
  orgDetail: state.organizationStore.orgDetail,
});

const mapDispatchToProps = dispatch => ({
  createDiscounts: payload => dispatch(createOrganizationDiscount(payload)),
  updateDiscounts: payload => dispatch(bulkUpdateOrgDiscounts(payload)),
  deleteDiscounts: payload => dispatch(bulkDeleteOrgDiscounts(payload)),
});

export default connect(mapStateToProps, mapDispatchToProps)(OrgEditDiscountPage);