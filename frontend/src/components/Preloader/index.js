import React from 'react';
import * as classnames from 'classnames';
import './index.scss';

const Preloader = ({ className, style }) => (
  <div className={classnames("preloader", className)} style={style} >
    <svg version="1.0" width="64px" height="64px" viewBox="0 0 128 128" className="preloader__icon" >
        <g>
          <path d="M59.6 0h8v40h-8V0z" fill="#005386" fillOpacity="1"/>
          <path d="M59.6 0h8v40h-8V0z" fill="#ccdde7" fillOpacity="0.2" transform="rotate(30 64 64)"/>
          <path d="M59.6 0h8v40h-8V0z" fill="#ccdde7" fillOpacity="0.2" transform="rotate(60 64 64)"/>
          <path d="M59.6 0h8v40h-8V0z" fill="#ccdde7" fillOpacity="0.2" transform="rotate(90 64 64)"/>
          <path d="M59.6 0h8v40h-8V0z" fill="#ccdde7" fillOpacity="0.2" transform="rotate(120 64 64)"/>
          <path d="M59.6 0h8v40h-8V0z" fill="#b2cbda" fillOpacity="0.3" transform="rotate(150 64 64)"/>
          <path d="M59.6 0h8v40h-8V0z" fill="#99bacf" fillOpacity="0.4" transform="rotate(180 64 64)"/>
          <path d="M59.6 0h8v40h-8V0z" fill="#7fa9c2" fillOpacity="0.5" transform="rotate(210 64 64)"/>
          <path d="M59.6 0h8v40h-8V0z" fill="#6698b6" fillOpacity="0.6" transform="rotate(240 64 64)"/>
          <path d="M59.6 0h8v40h-8V0z" fill="#4c86aa" fillOpacity="0.7" transform="rotate(270 64 64)"/>
          <path d="M59.6 0h8v40h-8V0z" fill="#33759e" fillOpacity="0.8" transform="rotate(300 64 64)"/>
          <path d="M59.6 0h8v40h-8V0z" fill="#196492" fillOpacity="0.9" transform="rotate(330 64 64)"/>
          <animateTransform attributeName="transform" type="rotate" values="0 64 64;30 64 64;60 64 64;90 64 64;120 64 64;150 64 64;180 64 64;210 64 64;240 64 64;270 64 64;300 64 64;330 64 64" calcMode="discrete" dur="1080ms" repeatCount="indefinite" />
        </g>
      </svg>
  </div>
);

export default Preloader;