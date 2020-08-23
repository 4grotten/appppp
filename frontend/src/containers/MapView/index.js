import React, { createRef } from 'react';
import * as classnames from 'classnames';
import { Map, TileLayer, Marker, Popup } from 'react-leaflet'
import MobileTopHeader from '../../components/MobileTopHeader';
import Button from '../../components/UI/Button';
import './index.scss';

class MapView extends React.Component {
  constructor(props) {
    super(props);
    const { position, userGEO } = props;
    this.state = {
      hasLocation: false,
      lat: (position && position[0]) || userGEO.lat,
      lng: (position && position[1]) || userGEO.ltd,
      zoom: 50,
    }
  }

  mapRef = createRef();

  onMapClick = (e) => {
    e.stopPropagation();
    this.props.onChange && this.props.onChange({lat: this.state.lat, lng: this.state.lng});
  }

  handleClick = (e) => {
    const map = this.mapRef.current
    if (map != null && this.props.onChange) {
     this.setState({...this.state, ...e.latlng});
     map.leafletElement.locate()
    }
  }

  handleLocationFound = (e) => {
    if (!this.state.hasLocation && !this.props.position) {
      this.setState({
        ...this.state,
        hasLocation: true,
        ...e.latlng
      })
    }
  }

  render() {
    const { buttonLabel, onClick, editMode } = this.props;
    const position = [this.state.lat, this.state.lng];
    const marker = (this.state.lat && this.state.lng) ? (
      <Marker position={position}>
        <Popup>You are here</Popup>
      </Marker>
    ) : null

    return (
     <div className="map-view">
       <MobileTopHeader
         title="На карте"
         onBack={this.props.onBack}
       />
       <div className={classnames("map-view__map ", editMode && "map-view__map-full")}>
         <Map
           center={position}
           zoom={this.state.zoom}
           style={{ width: '100%', height: '100%'}}
           onLocationfound={this.handleLocationFound}
           onClick={this.handleClick}
           ref={this.mapRef}
         >
           <TileLayer
             attribution='&copy <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
             url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
           />
           {marker}
         </Map>
         <div className="map-view__bottom">
           <div className="container">
             <Button onClick={onClick || this.onMapClick} label={buttonLabel || "Отметить на карте"} className="map-view__button" type="button" />
           </div>
         </div>
       </div>
     </div>
    )
  }
}

export default MapView;