import React from 'react';
import * as classnames from 'classnames';
import UserCard from '../Cards/UserCard';
import TruncatedText from '../UI/TruncatedText';
import {prettyDate} from '../../common/utils';
import RecipientsCount from '../RecipientsCount';
import OrganizationCard from '../Cards/OrganizationCard';
import './index.scss';

const Message = ({ message, className }) => {
  const { sender, content, created_at, organization, organization_address, receivers_count, receivers, sender_role } = message;
  return (
    <div className={classnames("message__wrap", className)}>
      <RecipientsCount
        recipients={receivers}
        recipients_count={receivers_count}
        className="message__recipients"
      />

      <div className="message__body">
        {organization && (
          <OrganizationCard
            id={organization.id}
            image={organization.image && organization.image.medium}
            title={organization.title}
            description={organization_address}
            className="message__organization"
          />
        )}
        {sender && (
          <UserCard
            avatar={sender.avatar}
            fullname={sender.full_name}
            description={sender_role || 'Собственник'}
            className="message__sender"
            smallSize
          />
        )}
        <TruncatedText lines={2} className="message__text f-15">
          {content}
        </TruncatedText>
      </div>
      <div className="message__time f-12">{prettyDate(created_at)}</div>
    </div>
  );
};

export default Message;