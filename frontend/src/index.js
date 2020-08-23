import * as React from 'react';
import * as ReactDOM from 'react-dom';
import App from './app';
import { Provider } from 'react-redux';
import { ConnectedRouter } from 'connected-react-router';
import store, { history } from './store/configureStore';
import { ToastContainer } from 'react-toastify';
import runtime from 'serviceworker-webpack-plugin/lib/runtime';

import 'normalize.css';
import 'react-toastify/dist/ReactToastify.min.css';
import './index.scss';

const app = (
  <Provider store={store}>
    <ConnectedRouter history={history}>
      <App />
      <ToastContainer />
    </ConnectedRouter>
  </Provider>
);

ReactDOM.render (app, document.getElementById("root"));

if ('serviceWorker' in navigator) {
  runtime.register();
}