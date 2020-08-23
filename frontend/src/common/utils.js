import moment from 'moment';
import {DATE_FORMAT_DD_MM_YYYY, DATE_FORMAT_YYYY_MM_DD} from './constants';
import qs from 'qs';

function fallbackCopyTextToClipboard(text, onSuccess, onFailure) {
  const textArea = document.createElement("textarea");
  textArea.value = text;

  // Avoid scrolling to bottom
  textArea.style.top = "0";
  textArea.style.left = "0";
  textArea.style.position = "fixed";

  document.body.appendChild(textArea);
  textArea.focus();
  textArea.select();

  try {
    const successful = document.execCommand('copy');
    const msg = successful ? 'successful' : 'unsuccessful';
    onSuccess && onSuccess(text, msg);
  } catch (err) {
    onFailure && onFailure(text, 'unsuccessful');
  }

  document.body.removeChild(textArea);
}
export const copyTextToClipboard = (text, onSuccess, onFailure) =>{
  if (!navigator.clipboard) {
    fallbackCopyTextToClipboard(text, onSuccess, onFailure);
    return;
  }
  navigator.clipboard.writeText(text).then(onSuccess, onFailure);
}

export const isMobile = {
  Android: function () {
    return navigator.userAgent.match(/Android/i);
  },
  BlackBerry: function () {
    return navigator.userAgent.match(/BlackBerry/i);
  },
  iOS: function () {
    return navigator.userAgent.match(/iPhone|iPad|iPod/i);
  },
  Opera: function () {
    return navigator.userAgent.match(/Opera Mini/i);
  },
  Windows: function () {
    return navigator.userAgent.match(/IEMobile/i);
  },
  any: function () {
    return (isMobile.Android() || isMobile.BlackBerry() || isMobile.iOS() || isMobile.Opera() || isMobile.Windows());
  }
};

export const parseLocation = ({ latitude, longitude }) => {
  if (latitude && longitude) {
    return  {
      lat: latitude,
      lng: longitude
    }
  }
  return null;
}

export const padNumber = (id, totalLength = 6) => {
  const zeros = new Array(totalLength).fill(0).join('')
  return !id
    ? zeros
    : (`${id}`.length >= totalLength
        ? `${id}`
        : (zeros + id).slice(totalLength * -1))
}

export const chunkArray = (arr, size) =>
  Array.from({ length: Math.ceil(arr.length / size) }, (v, i) =>
    arr.slice(i * size, i * size + size)
  );

export const getRandomElementFromArray = arr => arr[Math.floor(Math.random() * arr.length)];

export const dataURItoBlob = (dataURI, mime) => {
  // convert base64/URLEncoded data component to raw binary data held in a string
  let byteString;
  if (dataURI.split(',')[0].indexOf('base64') >= 0)
    byteString = atob(dataURI.split(',')[1]);
  else
    byteString = unescape(dataURI.split(',')[1]);

  // separate out the mime component
  const mimeString = mime || dataURI.split(',')[0].split(':')[1].split(';')[0];

  // write the bytes of the string to a typed array
  const ia = new Uint8Array(byteString.length);
  for (let i = 0; i < byteString.length; i++) {
    ia[i] = byteString.charCodeAt(i);
  }

  return new Blob([ia], {type:mimeString});
}

export const prettyDate = datetime => {
  const diff_sec = moment().diff(moment(datetime), 'second');
  const diff_day = moment().diff(moment(datetime), 'day');

  if (diff_day < 1) {
    if (diff_sec < 60) { return diff_sec < 1 ? 'только что' : `${diff_sec} с. назад`; }
    if (diff_sec < 120) { return `1 м. назад`; }
    if (diff_sec < 3600) { return `${Math.floor(diff_sec / 60)} м. назад`; }
    if (diff_sec < 7200) { return `1 ч. назад`; }
    if (diff_sec < 86400) { return `${Math.floor(diff_sec / 3600)} ч. назад`; }
  }

  return moment(datetime).format(DATE_FORMAT_DD_MM_YYYY);
}

export const dateRangeConverter = ({ start, end }) => {
  const formattedStart = start ? moment(start).format(DATE_FORMAT_YYYY_MM_DD) : null;
  const formattedEnd = end ? moment(end).format(DATE_FORMAT_YYYY_MM_DD) : null;
  return { start: formattedStart, end: formattedEnd };
}

export const getQuery = (params, exclude = ['showMenu', 'hasMore', 'step', 'title']) => {
  let datasets = '';
  if (params) {
    const filteredParams = { ...params, search: params.search ? params.search : null };
    exclude.map(key => { delete filteredParams[key]} );
    datasets = qs.stringify({...filteredParams, ...dateRangeConverter(filteredParams)}, { strictNullHandling: true, skipNulls: true })
    if (datasets) {
      return `?${datasets}`
    }
  }
  return '';
}

export const getUUID = () => {
  const navigator_info = window.navigator;
  const screen_info = window.screen;
  let uid = navigator_info.mimeTypes.length;
  uid += navigator_info.userAgent.replace(/\D+/g, '');
  uid += navigator_info.plugins.length;
  uid += screen_info.height || '';
  uid += screen_info.width || '';
  uid += screen_info.pixelDepth || '';
  return uid;
}