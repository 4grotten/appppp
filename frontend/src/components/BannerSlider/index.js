import React from 'react';
import * as classnames from 'classnames';
import ReactIdSwiper from 'react-id-swiper/lib/ReactIdSwiper.custom';
import { Swiper } from 'swiper/swiper.esm.js';
import BannerLocal from '../BannerLocal';
import {BANNER_BACKGROUNDS} from '../../common/constants';
import './index.scss';

const params = {
  Swiper,
  modules: [],
  slidesPerView: 'auto',
  centeredSlides: true,
  loop: true,
  spaceBetween: 40,
}

const BannerSlider = ({ banners, className }) => {
  return (
    <div className={classnames("banner-slider", className)}>
      <ReactIdSwiper {...params} >
        {banners.map((banner, index) => (
          <div key={index} className="banner-slider__slide">
            <BannerLocal
              banner={banner}
              background={BANNER_BACKGROUNDS[index % BANNER_BACKGROUNDS.length]}
            />
          </div>
        ))}
      </ReactIdSwiper>
    </div>
  );
};

export default BannerSlider;