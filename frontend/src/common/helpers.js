import {ERROR_MESSAGES, MESSAGE} from './messages';

export const readURL = image => {
  return new Promise((resolve, reject) => {
    try {
      const reader = new FileReader();
      reader.onload = e => {
        resolve(e.target.result);
      };
      reader.readAsDataURL(image);
    } catch (e) {
      reject();
    }
  });
};

export const PHONE_NUMBER = /^[+*][0-9]*$/g
export const PROTOCOL_REGEX = /^(http:\/\/|https:\/\/)/g
// export const URL_PARSER = /^((http[s]?|ftp):\/)?\/?([^:\/\s]+)((\/\w+)*\/)([\w\-\.]+[^#?\s]+)(.*)?(#[\w\-]+)?$/g
export const URL_PARSER = /^((http[s]?|ftp):\/)?\/?([^:\/\s]+)(:([^\/]*))?((\/\w+)*\/)([\w\-\.]+[^#?\s]+)(\?([^#]*))?(#(.*))?$/g
export const VALID_DISCOUNT = /^[1-9][0-9]?$|^100$/g // RegEx from 1-100 decimal number
export const DECIMAL_DIGITS = /^\d*\.?\d*$/g // RegEx from 51.67;
export const ONLY_DIGITS = /^\d*$/g // RegEx from 124124;
export const getMessage = (res, customMsg) => {
  return (res && res.message) || customMsg || MESSAGE.smtw
};
export const getRandom = (min = 1, max = 100) => Math.floor(Math.random() * max) + min;
export const socialDetect = text => {
  if (text.includes('instagram.com')) {
    return 'instagram'
  }

  if (text.includes('facebook.com') || text.includes('fb.com')) {
    return 'facebook';
  }

  return text.replace(PROTOCOL_REGEX, '');
}

export const validateForSameDiscount = (discountList, isCumulative) => {
  if (discountList.length > 1) {
    const percents = [];
    const limits = [];
    const errorDiscount = new Array(discountList.length).fill(null);
    discountList.map((discount, index) => {
      if (index === 0) {
        isCumulative && limits.push(parseInt(discount.limit))
        return percents.push(parseInt(discount.percent))
      }

      if (!percents.includes(parseInt(discount.percent))) {
        percents.push(parseInt(discount.percent));
      } else {
        errorDiscount[index] = { percent: ERROR_MESSAGES.percent_duplicate };
      }

      if (isCumulative) {
        if (!limits.includes(parseInt(discount.limit))) {
          limits.push(parseInt(discount.limit));
        } else {
          errorDiscount[index] = errorDiscount[index] ? {...errorDiscount[index], limit: ERROR_MESSAGES.limit_duplicate} : { limit: ERROR_MESSAGES.limit_duplicate };
        }
      }
    });

    return !!errorDiscount.filter(item => item).length && errorDiscount;
  }
}

export const shortenNumber = num => {
  const digit = parseInt(num);
  if (!isNaN(digit)) {
    if (digit < 1000) { return digit; }
    if (digit < 1000000) { return `${(Math.floor(digit/1000))}k`; }
    return `${(Math.floor(digit/1000000))}m`
  }
  return 0;
}

export const checkForValidFile = (file, allowedTypes, allowedMaxSize, allowedMinSize) => {
  const result = { isValid: true };

  if (file) {
    const { type, size } = file;
    if (allowedTypes && !allowedTypes.includes(type)) {
      result.isValid = false;
      result.type = 'File type is invalid'
    }

    if (allowedMaxSize && size >= allowedMaxSize) {
      result.isValid = false;
      result.size = 'File size is too big'
    }

    if (allowedMinSize && size <= allowedMinSize) {
      result.isValid = false;
      result.size = 'File size is too small'
    }
  }

  return result;
}

export const getUserGEO = setUserGEO => {
  if ("geolocation" in navigator) {
    navigator.geolocation.getCurrentPosition(
      function success(position) {
        setUserGEO({lat:position.coords.latitude, ltd: position.coords.longitude});
      },
      function error(error_message) {
        fetch('http://ip-api.com/json').then(async response => {
          if (response.ok) {
            let data = await response.json();
            setUserGEO({ lat: data.lat, ltd: data.lon });
          }
        });
        console.warn('An error has occured while retrieving location', error_message)
      })
  } else {
    fetch('http://ip-api.com/json').then(async response => {
      if (response.ok) {
        let data = await response.json();
        setUserGEO({ lat: data.lat, ltd: data.lon });
      }
    });
  }
}