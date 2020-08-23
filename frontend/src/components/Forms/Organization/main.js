import React from 'react';
import MobileTopHeader from '../../MobileTopHeader';
import ImageUploader from '../../ImageUploader';
import TextareaField from '../../UI/TextareaField';
import {InputTextField} from '../../UI/InputTextField';
import TimeRangeField from '../../UI/TimeRangeField';
import RowButton from '../../UI/RowButton';
import {ContactIcon, WebIcon} from '../../UI/Icons';
import {CurrencyInput} from '../../UI/CurrencyInput';
import './index.scss';

const MainView = ({ formikBag, onBack, onMap, title, children, ...other }) => {
  const { values, handleChange, setFieldValue, errors, touched } = formikBag;
  return (
    <div className="organization-form-main">
      <MobileTopHeader
        title={title || "Новая организация"}
        onBack={onBack}
        {...other}
      />

      <div className="container">
        <div className="organization-form-main__preview">
          <ImageUploader
            onChange={file => setFieldValue('image', file)}
            image={values.image}
            imageURL={values.imageURL}
            error={errors.image && touched.image && errors.image}
            className="organization-form-main__preview-left"
          />
          <div className="organization-form-main__preview-right">
            <p className="tl f-12">{values.selectedTypes[0] && values.selectedTypes[0].title || 'Вид организации'}</p>
            <h2 className="tl f-20">{values.title || 'Название компании'}</h2>
          </div>
        </div>

        <TextareaField
          placeholder="Добавьте описание компании"
          name="description"
          value={values.description}
          onChange={handleChange}
          error={errors.description && touched.description && errors.description}
        />

        <InputTextField
          name="organizationType"
          label="Вид Организации"
          value={values.selectedTypes[0] && values.selectedTypes[0].title || ''}
          onClick={() => setFieldValue('step', 4)}
          onChange={() => null}
          error={errors.selectedTypes && touched.selectedTypes && errors.selectedTypes}
          showArrow
        />

        <InputTextField
          name="title"
          label="Название Организации"
          value={values.title}
          onChange={handleChange}
          error={errors.title && touched.title && errors.title}
        />

        <InputTextField
          name="address"
          label="Адрес"
          value={values.address}
          onChange={handleChange}
          error={errors.address && touched.address && errors.address}
          className="organization-form-main__map"
          onMap={onMap}
        />

        <TimeRangeField
          use24Hours={true}
          start={values.openAt}
          end={values.closeAt}
          onStartChange={(value) => setFieldValue('openAt', value)}
          onEndChange={(value) => setFieldValue('closeAt', value)}
          error={(errors.openAt || errors.closeAt) && (touched.openAt || touched.closeAt)  && (errors.openAt || errors.closeAt)}
        />

        <CurrencyInput
          name="currency"
          label="Валюта организации"
          value={values.country}
          onClick={() => setFieldValue('step', 6)}
          disabled
          error={errors.country && touched.country && errors.country}
        />

        <div className="organization-form-main__buttons">
          <RowButton label="Контакты" onClick={() => setFieldValue('step', 1)} >
            <ContactIcon />
          </RowButton>

          <RowButton label="Web / Социальные сети" onClick={() => setFieldValue('step', 2)} >
            <WebIcon />
          </RowButton>
        </div>
        {children}
      </div>
    </div>
  );
};

export default MainView;