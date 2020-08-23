import React from 'react';
import * as classnames from 'classnames';
import {Link} from 'react-router-dom';
import './index.scss';

const PartnersStatistic = ({ organization, partners, className, onClick }) => {
  const { count, list } = partners;

  return (
    <Link to={`/organizations/${organization}/partner-statistics`} className={classnames("partners-statistic", className)} onClick={onClick}>
      <h5 className="f-20 f-600">Статистика партнеров</h5>
      <div className="partners-statistic__image-container">
        {!count && 'У вас нет партнеров'}
        {list.map(partner => (
          <div className="partners-statistic__image" key={partner.id}>
            <img src={partner.image.small} alt={partner.title} />
          </div>
        ))}

        {count > 3 && (
          <div className="partners-statistic__counter">
            {`+${count - 3}`}
          </div>
        )}
      </div>
    </Link>
  );
};

export default PartnersStatistic;