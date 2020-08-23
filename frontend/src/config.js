const ENVIRONMENT = process.env.REACT_APP_ENV || 'production';
const DEV_API_URL = 'http://localhost:5000';
const API_URL = process.env.REACT_APP_API_URL || DEV_API_URL;
const PREFIX = '/api/v1';

const baseURL = window.location.origin.toString();
const getApiURL = API_URL => (ENVIRONMENT === 'development' ? DEV_API_URL : API_URL);

const config = {
    baseURL,
    apiURL: getApiURL(API_URL) + PREFIX,
};

export default config;