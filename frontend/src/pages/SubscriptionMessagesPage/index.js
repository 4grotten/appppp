import React from 'react';
import qs from 'qs';
import MobileTopHeader from '../../components/MobileTopHeader';
import Preloader from '../../components/Preloader';
import EmptyBox from '../../components/EmptyBox';
import InfiniteScroll from 'react-infinite-scroll-component';
import Message from '../../components/Message';
import {connect} from 'react-redux';
import {getSubscriptionMessages} from '../../store/actions/messageActions';
import './index.scss'

const DEFAULT_LIMIT = 10;

class SubscriptionMessagesPage extends React.Component {
  constructor(props) {
    super(props);
    const { org } = qs.parse(this.props.location.search.replace('?',''));
    this.state = {
      page: 1,
      limit: DEFAULT_LIMIT,
      organization: org || null,
      hasMore: true,
    }
  }

  componentDidMount() {
    this.props.getSubscriptionMessages(this.state);
  }

  getNext = totalPages => {
    if (this.state.page < totalPages) {
      const nextPage = this.state.page + 1
      this.props.getSubscriptionMessages({
        ...this.state,
        page: nextPage,
      }, true);

      return this.setState({ ...this.state, hasMore: true, page: nextPage })
    }
    this.setState({ ...this.state, hasMore: false });
  }

  render() {
    const { subscriptionMessages, history } = this.props;
    const { data, loading } = subscriptionMessages;
    const { page } = this.state;

    return (
      <div className="subscription-messages-page">
        <MobileTopHeader
          title="Сообщения"
          onBack={() => history.goBack()}
        />

        <div className="container">
          <div className="subscription-messages-page__content">
            {(page === 1 && loading)
              ?  <Preloader />
              : (!data || (data && !data.total_count))
                ? <EmptyBox title="Нет сообщений" description={'Данная организация не публиковала сообщения'} />
                : (
                  <InfiniteScroll
                    dataLength={Number(data.list.length) || 0}
                    next={() => this.getNext(data.total_pages)}
                    hasMore={this.state.hasMore}
                    loader={null}
                  >
                    {data.list.map(message => (
                      <Message
                        key={message.id}
                        message={message}
                        className="subscription-messages-page__message"
                      />
                    ))}
                  </InfiniteScroll>
                )}
          </div>
        </div>
      </div>
    );
  }
}

const mapStateToProps = state => ({
  subscriptionMessages: state.messageStore.subscriptionMessages,
})

const mapDispatchToProps = dispatch => ({
  getSubscriptionMessages: (params, isNext) => dispatch(getSubscriptionMessages(params, isNext)),

})

export default connect(mapStateToProps, mapDispatchToProps)(SubscriptionMessagesPage);