import React, {useState, useEffect, useRef} from "react";
import Navbar from "../components/navbar";
import Map, {NavigationControl, Source, Layer, MapProvider, useMap} from 'react-map-gl/maplibre';

const API_KEY = 'NM2bzuwan7L5ET5h10no';

function stationURL(bounds) {
    const boundsStr = `${bounds._sw.lng},${bounds._sw.lat},${bounds._ne.lng},${bounds._ne.lat}`;
    return `http://127.0.0.1:8000/geojson/stations?bounds=${boundsStr}`;
}

function LiveStationsSource({updateSourceCallback, id}) {
    const layerStyle = {
        id: 'point',
        type: 'circle',
        paint: {
            "circle-radius": ["case", ["get", "cluster"], 10, 5],
            'circle-color': '#007cbf'
        }
    };

    const {current: map} = useMap();
    const [bounds, setBounds] = useState(map.getBounds());
    const [stationSource, setStationSource] = useState(stationURL(bounds));

    updateSourceCallback(() => {
        setBounds(map.getBounds());
    });

    useEffect(() => {
        const stationTimeout = setTimeout(() => {
            console.log('updating station source');
            setStationSource(stationURL(bounds));
        }, 10);

        return () => clearTimeout(stationTimeout);
    }, [bounds]);

    return <Source id={id} type="geojson" data={stationSource}
                   cluster={true}
                   clusterRadius={20}
                   clusterMaxZoom={14}>
        <Layer {...layerStyle}/>
    </Source>
}

export default function MapRoute() {
    const [viewState, setViewState] = useState({
        longitude: -122.676483,
        latitude: 45.523064,
        zoom: 12
    });

    const mapMovedCallbackRef = useRef();

    const updateMap = (evt) => {
        setViewState(evt.viewState);
        if (mapMovedCallbackRef.current) mapMovedCallbackRef.current();
    }

    return <MapProvider>
        <Navbar/>
        <Map
            {...viewState}
            onMove={updateMap}
            style={{position: "absolute", top: "52px", width: "100%", height: " calc(100vh - 52px)"}}
            mapStyle={`https://api.maptiler.com/maps/streets-v2/style.json?key=${API_KEY}`}>
            <LiveStationsSource id="stations" updateSourceCallback={(cb) => mapMovedCallbackRef.current = cb}/>
            <NavigationControl position="top-right"/>
        </Map>
    </MapProvider>
}
