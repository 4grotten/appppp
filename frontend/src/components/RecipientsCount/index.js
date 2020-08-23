import React from 'react';
import * as classnames from 'classnames';
import Avatar from '../UI/Avatar';
import './index.scss';

const RecipientsCount = ({ recipients, recipients_count, className }) => {
  return (
    <div className={classnames("recipients-count", className)}>
      <div className="recipients-count__group">
        {recipients && recipients.map(recipient => (
          <Avatar
            key={recipient.id}
            size={25}
            src={recipient.avatar && recipient.avatar.medium}
            alt={recipient.full_name}
            className="recipients-count__group-avatar"
            withBorder
          />
        ))}
      </div>
      <div className="recipients-count__text f-14">{recipients_count || 0} получателей</div>
    </div>
  );
};

export default RecipientsCount;