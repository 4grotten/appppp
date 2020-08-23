import Cookie from 'js-cookie';

export const saveToCookie = (state, config = {}) => {
  try {
    Cookie.set('state', state, config);
  } catch (e) {
    console.warn('Could not save state');
  }
};

export const loadFromCookie = () => {
  try {
    const serializedState = Cookie.get('state');
    if (serializedState === null) {
      return undefined;
    }
    return JSON.parse(serializedState);
  } catch (e) {
    return undefined;
  }
};