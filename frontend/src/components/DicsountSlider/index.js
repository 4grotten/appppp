import React from 'react';
import * as classnames from 'classnames';
import ReactIdSwiper from 'react-id-swiper/lib/ReactIdSwiper.custom';
import { Swiper, Navigation, Pagination } from 'swiper/swiper.esm.js';
import './index.scss';

const params = {
  Swiper,
  modules: [Navigation, Pagination],
  pagination: {
    el: '.swiper-pagination',
    type: 'bullets',
    clickable: true
  },
  spaceBetween: 30
}

const DiscountSlider = ({ clientStatus, children, cards, className, slideClassName}) => {
  const swiperRef = React.useRef(null);
  const [currentIndex, setIndex] = React.useState(0);

  React.useEffect(() => {
    if (swiperRef !== null) {
      swiperRef.current.swiper.on("slideChange", () => setIndex(swiperRef.current.swiper.realIndex));
    }

    return () => {
      if (swiperRef !== null) {
        swiperRef.current.swiper.off("slideChange", () => setIndex(swiperRef.current.swiper.realIndex));
      }
    };
  }, [swiperRef]);

  return (
    <div className={classnames("discount-slider", className)}>
      <ReactIdSwiper {...params} ref={swiperRef}>
        {children.map((card, index) => (
          <div key={index} className={slideClassName}>{card}</div>
        ))}
      </ReactIdSwiper>

      {clientStatus && (
        <div className="discount-slider__earned f-14">
          Накоплено: <span>{clientStatus && Math.floor(clientStatus.total_spent) || 0}</span> <span>/</span> <span>{cards[currentIndex] && Math.round(cards[currentIndex].limit)} {cards[currentIndex].currency}</span>
        </div>
      )}
    </div>
  )
}

export default DiscountSlider;