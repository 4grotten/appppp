import React from 'react';
import Swiper from 'react-id-swiper';

import 'swiper/swiper.scss';

const Pagination = () => {
  const params = {

    pagination: {
      el: '.swiper-pagination',
      clickable: true
    }
  }
  return (
    <Swiper {...params} className='.swiper-pagination'>
      <div>Slide #1</div>
      <div>Slide #2</div>
      <div>Slide #3</div>
      <div>Slide #4</div>
      <div>Slide #5</div>
    </Swiper>
  )
};
export default Pagination;