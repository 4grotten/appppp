import React from 'react';
import MobileTopHeader from '../../components/MobileTopHeader';
import {ArrowRight} from '../../components/UI/Icons';
import './index.scss';

const OrganizationTypesView = ({ onBack, orgTypes, selectedTypes, onSelect }) => {
  const { data } = orgTypes;
  return (
    <div className="org-types-view">
      <MobileTopHeader
        onBack={onBack}
        title="Вид Организации"
      />
      <div className="container">
        <div  className="org-types-view__cards">
          {data && data.map(cat => (
            <div key={cat.id} className="org-types-view__card row" onClick={() => onSelect(cat.id)}>
              <div className="org-types-view__card-left">
                <p className="f-16 tl">{cat.name}</p>
                <p className="f-14">{cat.types.filter(type => selectedTypes.map(item => item.id).includes(type.id)).map(type => type.title).join(', ')}</p>
              </div>
              <ArrowRight />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default OrganizationTypesView;