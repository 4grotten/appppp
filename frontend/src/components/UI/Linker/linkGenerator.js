import {isMobile} from '../../../common/utils';
import qs from 'qs';

export const INSTAGRAM_RESOURCES = ['instagram.com', 'www.instagram.com'];
export const FACEBOOK_RESOURCES = ['facebook.com', 'www.facebook.com'];
export const YOUTUBE_RESOURCES = ['youtube.com', 'www.youtube.com', 'youtu.be', 'www.youtu.be'];
export const TIKTOK_RESOURCES = ['tiktok.com', 'www.tiktok.com'];

export const deepLink = url => {
  if (INSTAGRAM_RESOURCES.includes(url.resource)) {
    return generateInstagramLink(url);
  }

  if (FACEBOOK_RESOURCES.includes(url.resource)) {
    return generateFacebookLink(url);
  }

  if (YOUTUBE_RESOURCES.includes(url.resource)) {
    return generateYoutubeLink(url);
  }

  if (TIKTOK_RESOURCES.includes(url.resource)) {
    return generateTikTokLink(url);
  }

  if (!url.resource) {
    return `https://www.google.com/search?q=${url.href}`
  }

  return url.href;
};

export const generateInstagramLink = ({ pathname, href }) => {
  if (isMobile.iOS()) {
    return `instagram://user?username=${pathname.replace('/', '')}`
  }
  if (isMobile.Android()) {
    return `intent://www.instagram.com${pathname}#Intent;package=com.instagram.android;scheme=https;end`
  }
  return href;
};

export const generateFacebookLink = ({ pathname, href, search }) => {
  if (pathname.match(/^\/profile\//)) {
    const { id } = qs.parse(search);
    if (id) {
      if (isMobile.iOS()) {
        return `fb://page/?id=${id}`
      }

      if (isMobile.Android()) {
        return `intent://page/${id}?referrer=app_link#Intent;package=com.facebook.katana;scheme=fb;end`
      }
    }
  }
  return href;
};

export const generateYoutubeLink = ({ pathname, href }) => {
  const profileRegex = /^\/c\//;
  if (pathname.match(profileRegex)) {
    if (isMobile.iOS()) { return `vnd.youtube://${pathname.replace(profileRegex, '/user/')}`}
    if (isMobile.Android()) { return `intent://www.youtube.com${pathname.replace(profileRegex, '/user/')}#Intent;package=com.google.android.youtube;scheme=https;end`}
  }

  if (isMobile.iOS()) { return `vnd.youtube://user/`}
  if (isMobile.Android()) { return `intent://www.youtube.com/user/#Intent;package=com.google.android.youtube;scheme=https;end`}

  return href;
}

export const generateTikTokLink = ({ pathname, href }) => {
  if (pathname.match(/^\/@/)) {
    if (isMobile.iOS()) { return `snssdk1233://user/profile${pathname}`}
    if (isMobile.Android()) { return `intent://user/profile${pathname}#Intent;package=com.zhiliaoapp.musically;scheme=snssdk1233;end`}
  }

  return href;
}