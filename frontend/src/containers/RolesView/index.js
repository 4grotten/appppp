import React from 'react';
import {connect} from 'react-redux';
import InfiniteScroll from 'react-infinite-scroll-component';
import MobileTopHeader from '../../components/MobileTopHeader';
import Option from '../../components/UI/Option';
import {getRoles} from '../../store/actions/employeeActions';
import Preloader from '../../components/Preloader';
import EmptyBox from '../../components/EmptyBox';
import Button from '../../components/UI/Button';
import './index.scss';

class RolesView extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      page: 1,
      limit: 10,
      organization: props.organizationID,
      hasMore: true
    }
  }

  componentDidMount() {
    this.props.getRoles(this.state);
  }

  getNext = totalPages => {
    if (this.state.page < totalPages) {
      const nextPage = this.state.page + 1
      this.props.getRoles({
        ...this.state,
        page: nextPage,
      }, true);

      return this.setState({ ...this.state, hasMore: true, page: nextPage })
    }
    this.setState({ ...this.state, hasMore: false });
  }

  render() {
    const { roles, onBack, onSelect, onAddRole, selection } = this.props;
    const { page } = this.state;
    const { data, loading } = roles;

    return (
      <div className="roles-view">
        <MobileTopHeader
          title="Выбрать должность"
          onBack={onBack}
        />


        <div className="container">
          <div className="roles-view__content">
            {(page === 1 && loading)
              ?  <Preloader />
              : (!data || (data && !data.total_count))
                ? <EmptyBox title="Нет должностей" />
                : (
                  <InfiniteScroll
                    dataLength={Number(data.list.length) || 0}
                    next={() => this.getNext(data.total_pages)}
                    hasMore={this.state.hasMore}
                    loader={null}
                  >
                    {data.list.map(role => (
                      <Option
                        key={role.id}
                        label={role.title}
                        active={selection === role.id}
                        onSelect={() => onSelect(role)}
                        className="roles-view__card"
                      />
                    ))}
                  </InfiniteScroll>
                )}

            {onAddRole && (
              <Button
                label="Добавить должность"
                onClick={onAddRole}
                className="roles-view__add"
              />
            )}
          </div>
        </div>
      </div>
    );
  }
}

const mapStateToProps = state => ({
  roles: state.employeeStore.roles,

})

const mapDispatchToProps = dispatch => ({
  getRoles: (params, isNext) => dispatch(getRoles(params, isNext)),
})

export default connect(mapStateToProps, mapDispatchToProps)(RolesView);