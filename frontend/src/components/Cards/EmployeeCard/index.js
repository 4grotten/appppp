import React from 'react';
import * as classnames from 'classnames';
import {Link} from 'react-router-dom';
import './index.scss'

const EmployeeCard = ({ employee, className }) => {
  if (!employee) { return null; }
  const { id, user, role, active } = employee;
  return (
    <Link
      to={`employees/${id}`}
      className={classnames("employee-card", className)}
    >
      <div className="employee-card__top">
        <div className={classnames(
          "employee-card__avatar",
          (typeof active === "boolean") && (active ? "employee-card__avatar-active" : "employee-card__avatar-inactive"))
        }>
          <div className="employee-card__avatar-inner">
            <img src={user && user.avatar && user.avatar.medium} alt={user && user.full_name} />
          </div>
        </div>

        <div className="employee-card__content">
          <div className="employee-card__title f-16">{user && user.full_name}</div>
          <div className="employee-card__role f-14">{role && role.title}</div>
          <div className="employee-card__attendance row f-12">
            <div>03/09/2019</div>
            <div>08:00</div>
          </div>
        </div>
      </div>

      <div className="employee-card__id f-14 f-600">ID {user.id}</div>
    </Link>
  );
};

export default EmployeeCard;