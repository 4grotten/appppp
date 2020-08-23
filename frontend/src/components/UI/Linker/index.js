import React from 'react';
import parseUrl from 'parse-url';
import {LINK_TYPES} from '../../../common/constants';
import {deepLink} from './linkGenerator';
import './index.scss';

const Linker = ({ type, value }) => {
  let domain = '';
  const params = { target: "_blank" }

  if (type === LINK_TYPES.phone) {
    params.href = `tel:${value}`;
  }

  if (type === LINK_TYPES.web) {
    const url = parseUrl(value);
    domain = url.resource;
    params.href = deepLink(url);
  }

  return (
    <a {...params} className="linker f-600 f-14 tl">
      {domain || value}
    </a>
  );
};

export default Linker;