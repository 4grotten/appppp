import React from 'react';
import MobileTopHeader from '../../components/MobileTopHeader';
import PartnerCard from '../../components/Cards/PartnerCard';
import './index.scss';

const PartnersView = (props) => {
  const { onBack } = props;

  React.useEffect(() => {
    window.scrollTo(0, 0);
  }, []);

  return (
    <div className="partners-view">
      <MobileTopHeader
        onBack={onBack}
        title="Партнеры"
      />
      <div className="container">
        <div className="partners-view__summary row">
          <div className="f-14">Сумма: <span className="f-600">1000000</span></div>
          <div className="f-14">Экономия: <span className="f-600">14300</span></div>
        </div>

        <div className="partners-view__date">
          <div className="container">
            <span className="f-14">19 июня 2018 - 19 июня 2020</span>
          </div>
        </div>

        <div className="partners-view__list">
          <PartnerCard className="partners-view__list-item" />
          <PartnerCard className="partners-view__list-item" />
          <PartnerCard className="partners-view__list-item" />
          <PartnerCard className="partners-view__list-item" />
          <PartnerCard className="partners-view__list-item" />
          <PartnerCard className="partners-view__list-item" />
        </div>
      </div>
    </div>
  );
};

export default PartnersView;