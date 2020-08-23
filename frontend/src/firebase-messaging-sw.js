importScripts('https://www.gstatic.com/firebasejs/7.17.1/firebase-app.js');
importScripts('https://www.gstatic.com/firebasejs/7.17.1/firebase-messaging.js');

firebase.initializeApp({
  apiKey: "AIzaSyAm0F7vk26fsSPh2gNCxrWxo3IiD2ptSqI",
  authDomain: "qrcode-c45c7.firebaseapp.com",
  databaseURL: "https://qrcode-c45c7.firebaseio.com",
  projectId: "qrcode-c45c7",
  storageBucket: "qrcode-c45c7.appspot.com",
  messagingSenderId: "802231326985",
  appId: "1:802231326985:web:ac44c3167598dc6a765bd8",
  measurementId: "G-3S5JN9CB81"
});

const messaging = firebase.messaging();

messaging.setBackgroundMessageHandler(payload => {
  const title = payload.notification.title;
  console.log('payload', payload.notification.icon);
  const options = {
    body: payload.notification.body,
    icon: payload.notification.icon
  }
  return self.registration.showNotification(title, options);
})