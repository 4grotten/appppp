import React, {Component} from 'react';
import MessageForm from '../../components/Forms/MessageForm';
import {connect} from 'react-redux';
import {createOrgMessage, getOrgRecipientsCount} from '../../store/actions/messageActions';

class MessageCreatePage extends Component {
  organization = this.props.match.params.id;

  componentDidMount() {
    this.props.getOrgRecipientsCount(this.organization);
  }

  onSubmit = values => {
    const payload = {
      content: values.text
    }

    this.props.createOrgMessage(this.organization, payload).then(res => {
      if (res && res.success) {
        this.props.history.push(`/organizations/${this.organization}/messages`)
      }
    })
  }

  render() {
    const { orgRecipientsCount, history } = this.props;
    return (
      <div className="message-create-page">
          <MessageForm
            onBack={() => history.push(`/organizations/${this.organization}/messages`)}
            recipients={orgRecipientsCount}
            organization={this.organization}
            onSubmit={this.onSubmit}
          />
      </div>
    );
  }
}

const mapStateToProps = state => ({
  orgRecipientsCount: state.messageStore.orgRecipientsCount,
})

const mapDispatchToProps = dispatch => ({
  createOrgMessage: (orgID, payload) => dispatch(createOrgMessage(orgID, payload)),
  getOrgRecipientsCount: (orgID) => dispatch(getOrgRecipientsCount(orgID)),
})

export default connect(mapStateToProps, mapDispatchToProps)(MessageCreatePage);