import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

import en from './locales/en.json';
import ru from './locales/ru.json';
import de from './locales/de.json';
import tr from './locales/tr.json';
import zh from './locales/zh.json';
import ar from './locales/ar.json';
import es from './locales/es.json';

const savedLanguage = localStorage.getItem('language') || 'system';
const supportedLangs = ["en", "ru", "de", "tr", "zh", "ar", "es"];

const getInitialLanguage = () => {
  if (savedLanguage === 'system') {
    const browserLang = navigator.language.split('-')[0];
    return supportedLangs.includes(browserLang) ? browserLang : 'en';
  }
  return savedLanguage;
};

i18n
  .use(initReactI18next)
  .init({
    resources: {
      en: { translation: en },
      ru: { translation: ru },
      de: { translation: de },
      tr: { translation: tr },
      zh: { translation: zh },
      ar: { translation: ar },
      es: { translation: es },
    },
    lng: getInitialLanguage(),
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false,
    },
  });

export default i18n;
