import React from 'react';
import * as classnames from 'classnames';
import { QRCode } from 'react-qr-svg';
import Avatar from '../../components/UI/Avatar';
import {QR_PREFIX} from '../../common/constants';
import {ShareIcon} from '../UI/Icons';
import './index.scss';

const MyQR = ({ user, open }) => (
  <div className={classnames("my-qr", open && "my-qr__open")}>
    <div className="container">
      <div className="my-qr__share">
        <ShareIcon />
      </div>

      <div className="my-qr__content">
        <div className="my-qr__user">
          <Avatar
            alt={user.full_name}
            src={user.avatar && user.avatar.large}
            gender={user.gender}
            className="my-qr__avatar"
          />
          <h2 className="f-20 f-800">{user.full_name}</h2>
        </div>

        <div className="my-qr__code">
          <QRCode
            bgColor="#FFFFFF"
            fgColor="#4285F4"
            level="H"
            style={{ width: 250 }}
            value={`${QR_PREFIX}${user.id}`}
          />
        </div>

        <p className="my-qr__id f-20 f-600">ID {user.id}</p>
      </div>
    </div>
  </div>
);

export default MyQR;