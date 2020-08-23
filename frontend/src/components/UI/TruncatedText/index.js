import React from 'react';
import * as classnames from 'classnames';
import PropTypes from 'prop-types';
import Truncate from 'react-truncate';
import './index.scss';

class TruncatedText extends React.Component {
  constructor(...args) {
    super(...args);

    this.state = {
      expanded: false,
      truncated: false
    };

    this.handleTruncate = this.handleTruncate.bind(this);
    this.toggleLines = this.toggleLines.bind(this);
  }

  handleTruncate(truncated) {
    if (this.state.truncated !== truncated) {
      this.setState({
        truncated
      });
    }
  }

  toggleLines(event) {
    event.preventDefault();

    this.setState({
      expanded: !this.state.expanded
    });
  }

  render() {
    const {
      children,
      more,
      less,
      lines,
      className
    } = this.props;

    const {
      expanded,
      truncated
    } = this.state;

    return (
      <p className={classnames("truncated-text", className)}>
        <Truncate
          lines={!expanded && lines}
          ellipsis={(
            <span>... <a href='#' onClick={this.toggleLines}>{more}</a></span>
          )}
          onTruncate={this.handleTruncate}
        >
          {children}
        </Truncate>
        {!truncated && expanded && (
          less && <span> <a href='#' onClick={this.toggleLines}>{less}</a></span>
        )}
      </p>
    );
  }
}

TruncatedText.defaultProps = {
  lines: 3,
  more: 'ещё',
  less: ''
};

TruncatedText.propTypes = {
  children: PropTypes.node.isRequired,
  lines: PropTypes.number,
  less: PropTypes.string,
  more: PropTypes.string,
  className: PropTypes.string
};

export default TruncatedText;