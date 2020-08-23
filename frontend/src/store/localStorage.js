export const saveToLocalStorage = state => {
  try {
    const serializedState = JSON.stringify(state);
    localStorage.setItem('state', serializedState);
  } catch (e) {
    console.warn('Could not save state');
  }
};

export const loadFromLocalStorage = () => {
  try {
    const serializedState = localStorage.getItem('state');
    if (serializedState === null) {
      return undefined;
    }

    return JSON.parse(serializedState);
  } catch (e) {
    return undefined;
  }
};

export const saveDataToLocalStorage = (key, value) => {
  try {
    const serializedValue = JSON.stringify(value);
    localStorage.setItem(key, serializedValue);
  } catch (e) {
    console.warn('Could not save state');
  }
}

export const getDataFromLocalStorage = key => {
  try {
    const data = localStorage.getItem(key);
    if (data === null) {
      return undefined;
    }

    return JSON.parse(data);
  } catch (e) {
    return undefined;
  }
}