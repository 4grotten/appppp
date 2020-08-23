import React, {Component} from 'react';
import MobileTopHeader from '../../components/MobileTopHeader';
import {Link} from 'react-router-dom';
import {MessageIcon} from '../../components/UI/Icons';
import Message from '../../components/Message';
import {connect} from 'react-redux';
import {getOrgMessages} from '../../store/actions/messageActions';
import Preloader from '../../components/Preloader';
import EmptyBox from '../../components/EmptyBox';
import InfiniteScroll from 'react-infinite-scroll-component';
import './index.scss';

const DEFAULT_LIMIT = 10;

class MessagesPage extends Component {
  constructor(props) {
    super(props);
    this.organization = props.match.params.id;
    this.state = {
      page: 1,
      limit: DEFAULT_LIMIT,
      hasMore: true,
    }
  }

  componentDidMount() {
    this.props.getOrgMessages(this.organization, this.state);
  }

  getNext = totalPages => {
    if (this.state.page < totalPages) {
      const nextPage = this.state.page + 1
      this.props.getOrgMessages(this.organization, {
        ...this.state,
        page: nextPage,
      }, true);

      return this.setState({ ...this.state, hasMore: true, page: nextPage })
    }
    this.setState({ ...this.state, hasMore: false });
  }

  render() {
    const { orgMessages, history } = this.props;
    const { page } = this.state;
    const { data, loading } = orgMessages;

    return (
      <div className="messages-page">
        <MobileTopHeader
          onBack={() => history.push(`/organizations/${this.organization}`)}
          title="Сообщения"
          renderRight={() => <Link to={`/organizations/${this.organization}/messages/create`} className="messages-page__icon"><MessageIcon /></Link>}
        />

        <div className="container">
          <div className="messages-page__content">
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
                        className="messages-page__message"
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
  orgMessages: state.messageStore.orgMessages,
})

const mapDispatchToProps = dispatch => ({
  getOrgMessages: (orgID, params, isNext) => dispatch(getOrgMessages(orgID, params, isNext)),
})

export default connect(mapStateToProps, mapDispatchToProps)(MessagesPage);