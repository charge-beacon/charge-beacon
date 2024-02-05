import React, {useRef, useState, useCallback} from "react";
import Navbar from "../components/navbar";
import Map, {MapProvider, Popup, NavigationControl, GeolocateControl} from 'react-map-gl/maplibre';
import LiveStationSource from "../components/map/LiveStationSource";

export const API_KEY = 'NM2bzuwan7L5ET5h10no';
const BASE_URL = '';

export default function MapRoute() {
    const [viewState, setViewState] = useState({
        longitude: -122.676483,
        latitude: 45.523064,
        zoom: 12
    });
    const [selectedStation, setSelectedStation] = useState(null);

    const mapMovedCallbackRef = useRef();
    const mapRef = useRef();

    const updateMap = (evt) => {
        setViewState(evt.viewState);
        if (mapMovedCallbackRef.current) mapMovedCallbackRef.current();
    }

    const onHover = useCallback(event => {
        const {features} = event;
        if (features && features.length) {
            if (mapRef.current) {
                mapRef.current.getCanvas().style.cursor = 'pointer';
            }
        } else {
            if (mapRef.current) {
                mapRef.current.getCanvas().style.cursor = '';
            }
        }
    }, []);

    const onClick = useCallback(event => {
        const {features} = event;
        if (!features || !features.length) return;

        // If a cluster is clicked, zoom in to the cluster
        if (features[0].properties.cluster) {
            const clusterId = features[0].properties.cluster_id;
            mapRef.current.getSource('stations').getClusterExpansionZoom(
                clusterId
            ).then((zoom, err) => {
                if (err) return;
                mapRef.current.easeTo({
                    center: features[0].geometry.coordinates,
                    zoom: zoom
                });
            });
            return;
        }

        // If a station is clicked, show the station popup
        const station = features[0];

        mapRef.current.easeTo({
            center: station.geometry.coordinates,
            zoom: 17
        });

        setSelectedStation({
            longitude: station.geometry.coordinates[0],
            latitude: station.geometry.coordinates[1],
            loading: true
        });

        // Fetch the station data
        fetch(`${BASE_URL}/station/${station.properties.beacon_name}.json`)
            .then(response => response.json())
            .then(data => {
                if (!data) return;
                setSelectedStation({
                    ...data,
                    loading: false
                });
            });
    }, []);

    let stationPopupContents = null;
    if (selectedStation !== null && selectedStation.loading) {
        stationPopupContents = (<strong>Loading...</strong>);
    } else if (selectedStation !== null) {
        console.log('selectedStation', selectedStation);
        stationPopupContents = (
            <div>
                <strong>{selectedStation.station_name}</strong>
                <br/>
                <em>
                    {selectedStation.street_address}<br/>
                    {selectedStation.city}, {selectedStation.state} {selectedStation.zip}
                </em>
            </div>
        );
    }

    return (
        <MapProvider>
            <Navbar/>
            <Map
                {...viewState}
                ref={mapRef}
                onMove={updateMap}
                onClick={onClick}
                onMouseMove={onHover}
                interactiveLayerIds={['stations-layer']}
                style={{position: "absolute", top: "52px", width: "100%", height: " calc(100vh - 52px)"}}
                mapStyle={`https://api.maptiler.com/maps/streets-v2/style.json?key=${API_KEY}`}>
                <LiveStationSource id="stations" updateSourceCallback={(cb) => mapMovedCallbackRef.current = cb}/>
                <NavigationControl position="top-right"/>
                <GeolocateControl position="top-right"/>
                {selectedStation != null &&
                    <Popup anchor="top"
                           offset={[0, 15]}
                           longitude={selectedStation.longitude}
                           latitude={selectedStation.latitude}
                           onClose={() => setSelectedStation(null)}>
                        {stationPopupContents}
                    </Popup>}
            </Map>
        </MapProvider>
    );
}
