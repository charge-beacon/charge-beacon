import React, {useRef, useEffect, useState} from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';

import Navbar from 'react-bootstrap/Navbar';
import Form from 'react-bootstrap/Form';

import Brand from './components/brand';

function App() {
    const mapContainer = useRef(null);
    const map = useRef(null);
    const [lng] = useState(-122.676483);
    const [lat] = useState(45.523064);
    const [zoom] = useState(12);
    const [API_KEY] = useState('NM2bzuwan7L5ET5h10no');

    useEffect(() => {
        if (map.current) return; // stops map from intializing more than once

        const getBoundsStr = () => {
            const bounds = map.current.getBounds();
            return `${bounds._sw.lng},${bounds._sw.lat},${bounds._ne.lng},${bounds._ne.lat}`;
        }

        map.current = new maplibregl.Map({
            container: mapContainer.current,
            style: `https://api.maptiler.com/maps/streets-v2/style.json?key=${API_KEY}`,
            center: [lng, lat],
            zoom: zoom
        });

        map.current.addControl(new maplibregl.NavigationControl(), 'top-right');

        map.current.on('load', () => {
            const boundsStr = getBoundsStr();
            map.current.addSource('stations', {
                type: 'geojson',
                data: `/geojson/stations?bounds=${boundsStr}`,
                cluster: true,
                clusterRadius: 20,
                clusterMaxZoom: 14,
            });
            map.current.addLayer({
                id: 'station-clusters',
                type: 'circle',
                source: 'stations',
                paint: {
                    "circle-color": "hsla(0,0%,0%,0.75)",
                    "circle-stroke-width": 1.5,
                    "circle-stroke-color": "white",
                    "circle-radius": ["case", ["get", "cluster"], 10, 5],
                }
            });
            map.current.addLayer({
                id: "station-counts",
                type: "symbol",
                source: "stations",
                layout: {
                    "text-font": ["Arial Bold"],
                    "text-field": ["get", "point_count"],
                    "text-offset": [0, 0.1] // move the label vertically downwards slightly to improve centering
                },
                paint: {
                    "text-color": "white"
                }
            });
        });

        const updateData = () => {
            const boundsStr = getBoundsStr();
            map.current.getSource('stations').setData(`/geojson/stations?bounds=${boundsStr}`);
        };

        map.current.on('moveend', updateData);

        map.current.on("mouseenter", "station-clusters", () => {
            map.current.getCanvas().style.cursor = "pointer";
        });

        map.current.on("mouseleave", "station-clusters", () => {
            map.current.getCanvas().style.cursor = "";
        });

        map.current.on('click', 'station-clusters', (e) => {
            const features = map.current.queryRenderedFeatures(e.point, {
                layers: ['station-clusters']
            });

            console.log('clicked on features', features);

            if (!features.length) return;

            if (features[0].properties.cluster) {
                console.log('cluster clicked', features[0].properties.cluster_id);
                const clusterId = features[0].properties.cluster_id;
                map.current.getSource('stations').getClusterExpansionZoom(
                    clusterId
                ).then((zoom, err) => {
                    if (err) return;
                    map.current.easeTo({
                        center: features[0].geometry.coordinates,
                        zoom: zoom
                    });
                });
            } else {
                const station = features[0];
                console.log('station clicked', station.properties);
                map.current.easeTo({
                    center: station.geometry.coordinates,
                    zoom: 17
                });
                const popup = new maplibregl.Popup()
                    .setLngLat(station.geometry.coordinates)
                    .setHTML(
                        `<strong>Loading...</strong>`
                    )
                    .addTo(map.current);

                fetch(`/station/${station.properties.beacon_name}.json`)
                    .then(response => response.json())
                    .then(data => {
                        console.log('station data', data);
                        if (!data || !popup.isOpen()) return;
                        popup.setHTML(
                            `<strong>${data.station_name}</strong><br>
                            <em>
                                ${data.street_address}<br>
                                ${data.city}, ${data.state} ${data.zip}
                            </em>`
                        );
                    });
            }
        });

    }, [API_KEY, lng, lat, zoom]);

    return (
        <div className="w-100 h-100 position-absolute">
            <Navbar expand="lg" fixed="top" className="bg-body-tertiary">
                <div className="w-100 px-3 d-flex flex-nowrap">
                    <Brand/>
                    <Form inline className="w-100">
                        <Form.Control
                            placeholder="Search for anything"
                            aria-label="Search"
                        />
                    </Form>
                </div>
            </Navbar>
            <div className="w-100 h-100 position-relative"
                 style={{paddingTop: '54px', height: 'calc(100vh - 54px)'}}>
                <div ref={mapContainer}
                     className="w-100 h-100 position-relative"
                />
            </div>
        </div>
    );
}

export default App;
