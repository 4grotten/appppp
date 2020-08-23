import React from 'react';
import * as classnames from 'classnames';
import ReactIdSwiper from 'react-id-swiper/lib/ReactIdSwiper.custom';
import { Swiper } from 'swiper/swiper.esm.js';
import OrganizationDscCard from '../Cards/OrganizationDscCard';
import {chunkArray} from '../../common/utils';
import {Link} from 'react-router-dom';
import './index.scss';

const params = {
  Swiper,
  modules: [],
  slidesPerView: 'auto',
  spaceBetween: 15,
}

const OrganizationSlider = ({ organizations, totalCount, category, className}) => {
  const organizationGroups = chunkArray(organizations, 3);
  const slides = organizationGroups.map((group, index) => (
    <div key={index} className="organization-slider__slide">
      {group.map(organization => (
        <OrganizationDscCard
          key={organization.id}
          organization={organization}
        />
      ))}
    </div>
  ))

  totalCount > organizations.length && slides.push((
    <div key="all" className="organization-slider__slide all">
      <Link className="organization-slider__all" to={`home/organizations?cat=${category.id}`}>
        <div>
          <p> Показать все</p>
          <p>{category.name}</p>
        </div>
      </Link>
    </div>
  ))

  return (
    <div className={classnames("organization-slider", className)}>
      <ReactIdSwiper {...params} >
        {slides}
      </ReactIdSwiper>
    </div>
  );
};

export default OrganizationSlider;