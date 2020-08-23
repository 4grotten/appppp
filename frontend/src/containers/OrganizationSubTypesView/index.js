import React from 'react';
import * as classnames from 'classnames';
import MobileTopHeader from '../../components/MobileTopHeader';
import './index.scss';

const OrganizationSubTypesView = ({ catID, orgTypes, selectedTypes, onBack, onNext, onSelect }) => {
  const { data } = orgTypes;
  const list = (data && data.filter(cat => cat.id === catID)) || [];

  React.useEffect(() => {
    window.scrollTo(0, 0);
  }, []);

  return (
    <div className="org-subtypes-view">
      <MobileTopHeader
        title="Вид Организации"
        onBack={onBack}
        onNext={onNext}
        nextLabel="Сохранить"
      />
      <div className="container">
        <div className="org-subtypes-view__cards">
          {!!list.length && (
            list[0].types.map(type => (
              <div
                key={type.id}
                className={classnames(
                  "org-subtypes-view__card",
                  "row",
                  selectedTypes.map(item => item.id).includes(type.id) && "org-subtypes-view__card-active")}
                onClick={() => onSelect(type)}
              >
                <p className="f-16 tl">{type.title}</p>
              </div>
            )))}
        </div>
      </div>
    </div>
  );
};

export default OrganizationSubTypesView;