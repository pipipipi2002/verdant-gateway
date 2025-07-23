import { h, Fragment } from 'preact';
import { useState } from 'preact/hooks';
import { route } from 'preact-router';

const DeviceCard = ({ device, latestTelemetry }) => {
    const [expanded, setExpanded] = useState(false);
    const [imageError, setImageError] = useState(false);

    const handleCardClick = (e) => {
        e.stopPropagation();
        setExpanded(!expanded);
    };

    const handleNavigate = (e) => {
        e.stopPropagation();
        route(`/device/${device.id}`);
    };

    const getStatusColor = () => {
        switch (device.status) {
        case 'online': return 'bg-green-500';
        case 'offline': return 'bg-red-500';
        case 'error': return 'bg-yellow-500';
        default: return 'bg-gray-500';
        }
    };

    return (
        <div 
            className="bg-white rounded-lg shadow hover:shadow-md transition-shadow cursor-pointer"
            onClick={handleCardClick}
        >
            <div className="p-6">
                <div className="flex">
                {/* Thumbnail */}
                    <div className="w-24 h-24 flex-shrink-0 mr-4">
                        {!imageError ? (
                            <img
                                src={device.snapshot_url || '/api/v1/devices/placeholder/snapshot'}
                                alt={device.plant_name}
                                className="w-full h-full object-cover rounded-lg"
                                onError={() => setImageError(true)}
                            />
                        ) : (
                            <div className="w-full h-full bg-gray-200 rounded-lg flex items-center justify-center">
                                <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                                </svg>
                            </div>
                        )}
                    </div>
                
                    {/* Device Info */}
                    <div className="flex-1">
                        <div className="flex justify-between items-start">
                            <div>
                                <h3 className="text-lg font-semibold text-gray-900">{device.name}</h3>
                                <p className="text-sm text-gray-600">{device.plant_name}</p>
                                
                                <div className="flex items-center mt-2">
                                    <div className={`w-2 h-2 rounded-full ${getStatusColor()} mr-2`}></div>
                                    <span className="text-sm text-gray-600">{device.status}</span>
                                </div>
                            </div>
                        
                            <button
                                onClick={handleNavigate}
                                className="ml-4 p-2 rounded-full hover:bg-gray-100 transition-colors"
                            >
                                <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                                </svg>
                            </button>
                        </div>
                        
                        {/* Basic Metrics */}
                        {latestTelemetry && (
                            <div className="mt-3 grid grid-cols-2 gap-2 text-sm">
                                <div>
                                    <span className="text-gray-500">Temp:</span>
                                    <span className="ml-1 font-medium">{latestTelemetry.soil_temperature.toFixed(2)}°C</span>
                                </div>
                                <div>
                                    <span className="text-gray-500">Humidity:</span>
                                    <span className="ml-1 font-medium">{latestTelemetry.soil_humidity.toFixed(2)}%</span>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
                
                {/* Expandable Content */}
                {expanded && (
                    <div className="mt-4 pt-4 border-t border-gray-200">
                        <div className="grid grid-cols-2 gap-3 text-sm">
                            <div>
                                <span className="text-gray-500">Location:</span>
                                <p className="font-medium">{device.location || 'Not set'}</p>
                            </div>
                            <div>
                                <span className="text-gray-500">Last Seen:</span>
                                <p className="font-medium">{new Date(device.last_seen).toLocaleString()}</p>
                            </div>
                            {latestTelemetry && (
                                <>
                                <div>
                                    <span className="text-gray-500">CO2:</span>
                                    <p className="font-medium">{latestTelemetry.co2.toFixed(2)} ppm</p>
                                </div>
                                <div>
                                    <span className="text-gray-500">Device Temp:</span>
                                    <p className="font-medium">{latestTelemetry.device_temperature.toFixed(2)}°C</p>
                                </div>
                                </>
                            )}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default DeviceCard;