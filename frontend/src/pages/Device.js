import { h } from 'preact';
import { useState, useEffect } from 'preact/hooks';
import { route } from 'preact-router';
import MetricChart from '../components/MetricChart';
import VideoStream from '../components/VideoStream';
import { apiClient } from '../services/api';
import { WebSocketClient } from '../services/websocket';

const Device = ({ deviceId }) => {
    const [device, setDevice] = useState(null);
    const [telemetryHistory, setTelemetryHistory] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [streamingVideo, setStreamingVideo] = useState(false);
    const [selectedMetric, setSelectedMetric] = useState('soil_temperature');
    const [showChart, setShowChart] = useState(false);
    const [wsClient, setWsClient] = useState(null);
    const [liveData, setLiveData] = useState(null);

    // Config state
    const [telemetryInterval, setTelemetryInterval] = useState(60);
    const [snapshotInterval, setSnapshotInterval] = useState(3600);

    useEffect(() => {
        fetchDeviceData();
        
        // Set up WebSocket for live telemetry
        const ws = new WebSocketClient();
        setWsClient(ws);
        
        ws.connectTelemetry(deviceId, (data) => {
            setLiveData(data);
            // Add to history
            setTelemetryHistory(prev => [...prev.slice(-99), data]);
        });

        return () => {
            ws.disconnect();
        };
    }, [deviceId]);

    const fetchDeviceData = async () => {
        try {
            const [deviceData, history] = await Promise.all([
                apiClient.getDeviceDetail(deviceId),
                apiClient.getTelemetryHistory(deviceId, 24)
            ]);
        
            setDevice(deviceData);
            setTelemetryHistory(history);
            setTelemetryInterval(deviceData.telemetry_interval);
            setSnapshotInterval(deviceData.snapshot_interval);
        } catch (err) {
            setError('Failed to load device data');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleCommand = async (command) => {
        try {
            await apiClient.sendCommand(deviceId, { command });
            alert(`Command "${command}" sent successfully`);
        } catch (err) {
            alert(`Failed to send command: ${err.message}`);
        }
    };

    const updateConfig = async () => {
        try {
            await apiClient.updateDeviceConfig(deviceId, {
                telemetry_interval: telemetryInterval,
                snapshot_interval: snapshotInterval
            });
            alert('Configuration updated successfully');
        } catch (err) {
            alert(`Failed to update config: ${err.message}`);
        }
    };

    const toggleVideoStream = () => {
        setStreamingVideo(!streamingVideo);
    };

    if (loading) {
        return (
            <div className="flex justify-center items-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-500"></div>
            </div>
        );
    }

    if (error || !device) {
        return (
            <div className="text-center py-12">
                <p className="text-red-600">{error || 'Device not found'}</p>
                <button
                    onClick={() => route('/')}
                    className="mt-4 px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
                >
                    Back to Farms
                </button>
            </div>
        );
    }

    const currentTelemetry = liveData || device.current_telemetry || {};

    return (
        <div>
            {/* Back Button */}
            <button
                onClick={() => route(`/farm/${device.farm_id}`)}
                className="mb-6 flex items-center text-gray-600 hover:text-gray-900"
            >
                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
                Back to Farm
            </button>

            {/* Device Header */}
            <div className="bg-white rounded-lg shadow p-6 mb-6">
                <div className="flex justify-between items-start">
                    <div>
                        <h2 className="text-2xl font-bold text-gray-900">{device.name}</h2>
                        <p className="text-gray-600">{device.plant_name}</p>
                        <p className="text-sm text-gray-500 mt-1">{device.location}</p>
                    </div>
                    <div className={`px-3 py-1 rounded-full text-white text-sm ${
                        device.status === 'online' ? 'bg-green-500' : 
                        device.status === 'offline' ? 'bg-red-500' : 'bg-yellow-500'
                    }`}>
                        {device.status.toUpperCase()}
                    </div>
                </div>

                {/* Device Info Grid */}
                <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                        <span className="text-gray-500">Firmware:</span>
                        <p className="font-medium">{device.firmware_version}</p>
                    </div>
                    <div>
                        <span className="text-gray-500">Uptime:</span>
                        <p className="font-medium">{device.uptime_hours.toFixed(1)} hours</p>
                    </div>
                    <div>
                        <span className="text-gray-500">Last Seen:</span>
                        <p className="font-medium">{new Date(device.last_seen).toLocaleString()}</p>
                    </div>
                    <div>
                        <span className="text-gray-500">Telemetry Today:</span>
                        <p className="font-medium">{device.total_telemetry_today}</p>
                    </div>
                </div>
            </div>

            {/* Main Content Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Left Column - Camera & Controls */}
                <div>
                    {/* Camera View */}
                    <div className="bg-white rounded-lg shadow p-6 mb-6">
                        <h3 className="text-lg font-semibold text-gray-900 mb-4">Camera View</h3>
                        
                        {streamingVideo ? (
                            <VideoStream deviceId={deviceId} onClose={toggleVideoStream} />
                        ) : (
                            <div className="relative">
                                <img
                                    src={device.snapshot_url}
                                    alt="Plant snapshot"
                                    className="w-full rounded-lg"
                                    onError={(e) => {
                                        e.target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjMwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iNDAwIiBoZWlnaHQ9IjMwMCIgZmlsbD0iI2VlZSIvPjx0ZXh0IHRleHQtYW5jaG9yPSJtaWRkbGUiIHg9IjIwMCIgeT0iMTUwIiBzdHlsZT0iZmlsbDojYWFhO2ZvbnQtd2VpZ2h0OmJvbGQ7Zm9udC1zaXplOjE5cHg7Zm9udC1mYW1pbHk6QXJpYWwsSGVsdmV0aWNhLHNhbnMtc2VyaWY7ZG9taW5hbnQtYmFzZWxpbmU6Y2VudHJhbCI+Tm8gSW1hZ2U8L3RleHQ+PC9zdmc+';
                                    }}
                                />
                                <button
                                    onClick={toggleVideoStream}
                                    className="mt-4 w-full px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
                                >
                                    Start Live Stream
                                </button>
                            </div>
                        )}
                    </div>

                    {/* Device Controls */}
                    <div className="bg-white rounded-lg shadow p-6">
                        <h3 className="text-lg font-semibold text-gray-900 mb-4">Device Controls</h3>
                    
                        <div className="space-y-3">
                            {device.commands_available.map(command => (
                            <button
                                key={command}
                                onClick={() => handleCommand(command)}
                                className="w-full px-4 py-2 bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
                            >
                                {command.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}
                            </button>
                            ))}
                        </div>

                        {/* Configuration */}
                        <div className="mt-6 pt-6 border-t border-gray-200">
                            <h4 className="font-medium text-gray-900 mb-3">Update Intervals</h4>
                    
                            <div className="space-y-3">
                                <div>
                                    <label className="block text-sm text-gray-600 mb-1">
                                        Telemetry Interval (seconds)
                                    </label>
                                    <input
                                        type="number"
                                        value={telemetryInterval}
                                        onChange={(e) => setTelemetryInterval(parseInt(e.target.value))}
                                        className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                                        min="10"
                                        max="3600"
                                    />
                                </div>
                        
                                <div>
                                    <label className="block text-sm text-gray-600 mb-1">
                                        Snapshot Interval (seconds)
                                    </label>
                                    <input
                                        type="number"
                                        value={snapshotInterval}
                                        onChange={(e) => setSnapshotInterval(parseInt(e.target.value))}
                                        className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                                        min="60"
                                        max="86400"
                                    />
                                </div>
                        
                                <button
                                    onClick={updateConfig}
                                    className="w-full px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
                                >
                                    Update Configuration
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Right Column - Telemetry */}
                <div>
                    {/* Current Telemetry */}
                    <div className="bg-white rounded-lg shadow p-6 mb-6">
                        <h3 className="text-lg font-semibold text-gray-900 mb-4">
                            Current Telemetry
                            {liveData && (
                                <span className="ml-2 text-xs text-green-500 animate-pulse">● LIVE</span>
                            )}
                        </h3>
                    
                        <div className="grid grid-cols-2 gap-4">
                            {Object.entries({
                                'Soil Temperature': currentTelemetry.soil_temperature || 'N/A',
                                'Soil Humidity': currentTelemetry.soil_humidity || 'N/A',
                                'CO2 Level': currentTelemetry.co2 || 'N/A',
                                'Device Temperature': currentTelemetry.device_temperature || 'N/A',
                                'Device Humidity': currentTelemetry.device_humidity || 'N/A',
                                'Status': currentTelemetry.status || 'N/A'
                            }).map(([label, value]) => (
                                <div key={label} className="bg-gray-50 rounded p-3">
                                    <p className="text-sm text-gray-500">{label}</p>
                                    <p className="text-lg font-semibold text-gray-900">{value}</p>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Historical Data */}
                    <div className="bg-white rounded-lg shadow p-6">
                        <h3 className="text-lg font-semibold text-gray-900 mb-4">Historical Data</h3>
                            
                        {/* Metric Selector */}
                        <div className="mb-4">
                            <select
                                value={selectedMetric}
                                onChange={(e) => setSelectedMetric(e.target.value)}
                                className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                            >
                                <option value="soil_temperature">Soil Temperature</option>
                                <option value="soil_humidity">Soil Humidity</option>
                                <option value="co2">CO2 Level</option>
                                <option value="device_temperature">Device Temperature</option>
                                <option value="device_humidity">Device Humidity</option>
                            </select>
                        </div>

                        <button
                            onClick={() => setShowChart(!showChart)}
                            className="w-full px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
                        >
                            {showChart ? 'Hide Chart' : 'Show Chart'}
                        </button>

                        {showChart && (
                            <div className="mt-4">
                                <MetricChart
                                data={telemetryHistory}
                                metric={selectedMetric}
                                title={selectedMetric.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}
                                />
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Device;