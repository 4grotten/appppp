import firebase from 'firebase/app';
import 'firebase/firebase-messaging';

const firebaseConfig = {
  apiKey: process.env.REACT_APP_FCM_API_KEY,
  authDomain: process.env.REACT_APP_FCM_AUTH_DOMAIN,
  databaseURL: process.env.REACT_APP_FCM_DB_URL,
  projectId: process.env.REACT_APP_FCM_PROJECT_ID,
  storageBucket: process.env.REACT_APP_FCM_STORAGE_BUCKET,
  messagingSenderId: process.env.REACT_APP_FCM_SENDER_ID,
  appId: process.env.REACT_APP_FCM_APP_ID,
  measurementId: process.env.REACT_APP_FCM_MEASUREMENT_ID
};

export function initializeFirebasePush(onPushMessage) {
  try {
    firebase.initializeApp(firebaseConfig);
    const messaging = firebase.messaging();
    messaging.onMessage(onPushMessage);
  } catch (e) {}
}

export async function getFCMToken() {
  try {
    const messaging = firebase.messaging();
    return messaging.getToken()
  } catch (e) { console.warn(e.message) }
}

export async function deleteFCMToken() {
  try {
    const messaging = firebase.messaging();
    const FCMToken = await getFCMToken();
    messaging.deleteToken(FCMToken)
      .then(res => {
        if (res) {
          localStorage.removeItem("fcm");
          console.warn('FCM removed');
        }
      })
      .catch(error => error);
  } catch (e) { console.warn(e.message) }
}