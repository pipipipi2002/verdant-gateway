import { h, Fragment } from 'preact';
import { useState, useEffect } from 'preact/hooks';
import { route } from 'preact-router';
import DeviceCard from '../components/DeviceCard';
import { apiClient } from '../services/api';

const Farm = ({ farmId }) => {
    const [farm, setFarm] = useState(null);
    const [devices, setDevices] = useState([]);
    const [telemetry, setTelemetry] = useState({});
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [lastUpdated, setLastUpdated] = useState(null);

    useEffect(() => {
        fetchFarmData();

        const telemetryInterval = setInterval(() => {
            if (devices.length > 0) {
                fetchTelemetry();
            }
        }, 10000); // Telemetry every 10s

        const resourceInterval = setInterval(() => {
            fetchResourceUsage();
        }, 15000); // Resource usage every 15s
        
        return () => {
            clearInterval(telemetryInterval);
            clearInterval(resourceInterval);
        };
    }, [farmId]);

    useEffect(() => {
        if (devices.length > 0) {
            fetchTelemetry();
        }
    }, [devices]);

    const fetchFarmData = async () => {
        try {
            // Only show loading on initial load, not on refresh
            setLoading(true);
            setError(null);    // Clear any previous errors
            
            const [farmData, devicesData] = await Promise.all([
                apiClient.getFarmDetail(farmId),
                apiClient.getDevices(farmId)
            ]);
            
            setFarm(farmData);
            setDevices(devicesData);
            setLastUpdated(new Date());
        } catch (err) {
            setError('Failed to load farm data');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const fetchResourceUsage = async() => {
        try {
            const farmData = await apiClient.getFarmDetail(farmId);
            setFarm(prevFarm => ({
                ...prevFarm,
                resource_utilization: farmData.resource_utilization
            }));
        } catch (err) {
            console.error('Failed to fetch resource usage:', err);
        }
    };

    const handleRefresh = () => {
        fetchFarmData();
    }

    const fetchTelemetry = async () => {
        try {
            const telemetryData = {};

            if (devices.length === 0) return;

            const promises = devices.map(device => 
                apiClient.getLatestTelemetry(device.id)
                .then(data => {
                    if (data) telemetryData[device.id] = data;
                })
                .catch(() => {}) // Ignore individual failures
            );
            
            await Promise.all(promises);
            setTelemetry(telemetryData);
        } catch (err) {
            console.error('Failed to fetch telemetry:', err);
        }
    };

    if (loading) {
        return (
            <div className="flex justify-center items-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-500"></div>
            </div>
        );
    }

    if (error || !farm) {
        return (
            <div className="text-center py-12">
                <p className="text-red-600">{error || 'Farm not found'}</p>
                <button
                    onClick={fetchFarmData}
                    className="mt-4 px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 mr-3"
                >
                    Retry
                </button>
                <button
                    onClick={() => route('/')}
                    className="mt-4 px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
                >
                    Back to Farms
                </button>
            </div>
        );
    }

    return (
        <div>
            {/* Back Button */}
            <button
                onClick={() => route('/')}
                className="mb-6 flex items-center text-gray-600 hover:text-gray-900"
            >
                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
                Back to Farms
            </button>

            {/* Farm Header */}
            <div className="bg-white rounded-lg shadow p-6 mb-6">
                <div className="flex justify-between items-start">
                    <div>
                        <h2 className="text-2xl font-bold text-gray-900">{farm.name}</h2>
                        <p className="text-gray-600 mt-1">{farm.location}</p>
                    </div>
                    <div className="flex items-center space-x-4">
                        {lastUpdated && (
                        <p className="text-xs text-gray-500">
                            Last updated: {lastUpdated.toLocaleTimeString()}
                        </p>
                        )}
                        <button
                            onClick={handleRefresh}
                            disabled={loading}
                            className="flex items-center px-3 py-2 bg-gray-100 text-gray-700 rounded hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            <svg 
                                className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} 
                                fill="none" 
                                stroke="currentColor" 
                                viewBox="0 0 24 24"
                            >
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                            </svg>
                            Refresh
                        </button>
                    </div>
                </div>
                
                <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-6">
                    {/* Device Summary */}
                    <div className="bg-gray-50 rounded-lg p-4">
                        <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider">
                        Device Status
                        </h3>
                        <div className="mt-3 grid grid-cols-3 gap-2 text-center">
                            <div>
                                <p className="text-2xl font-semibold text-gray-900">{farm.device_count}</p>
                                <p className="text-xs text-gray-500">Total</p>
                            </div>
                            <div>
                                <p className="text-2xl font-semibold text-green-600">{farm.active_devices}</p>
                                <p className="text-xs text-gray-500">Active</p>
                            </div>
                            <div>
                                <p className="text-2xl font-semibold text-red-600">{farm.offline_devices}</p>
                                <p className="text-xs text-gray-500">Offline</p>
                            </div>
                        </div>
                    </div>
                
                    {/* Gateway Info */}
                    <div className="bg-gray-50 rounded-lg p-4">
                        <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider">
                        Gateway Hardware
                        </h3>
                        <div className="mt-3 space-y-1 text-sm">
                            <p><span className="text-gray-500">Model:</span> {farm.gateway_hardware.model}</p>
                            <p><span className="text-gray-500">Memory:</span> {farm.gateway_hardware.memory}</p>
                            <p><span className="text-gray-500">Storage:</span> {farm.gateway_hardware.storage}</p>
                        </div>
                    </div>
                
                    {/* Resource Usage */}
                    <div className="bg-gray-50 rounded-lg p-4">
                        <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider">
                        Resource Usage
                        </h3>
                        <div className="mt-3 space-y-2">
                            <div>
                                <div className="flex justify-between text-sm">
                                    <span>CPU</span>
                                    <span>{farm.resource_utilization.cpu.toFixed(1)}%</span>
                                </div>
                                <div className="mt-1 bg-gray-200 rounded-full h-2">
                                    <div 
                                        className="bg-green-500 h-2 rounded-full"
                                        style={{ width: `${farm.resource_utilization.cpu}%` }}
                                    ></div>
                                </div>
                            </div>
                            <div>
                                <div className="flex justify-between text-sm">
                                    <span>Memory</span>
                                    <span>{farm.resource_utilization.memory.toFixed(1)}%</span>
                                </div>
                                <div className="mt-1 bg-gray-200 rounded-full h-2">
                                    <div 
                                        className="bg-blue-500 h-2 rounded-full"
                                        style={{ width: `${farm.resource_utilization.memory}%` }}
                                    ></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Devices Grid */}
            <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Devices</h3>
                <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                {devices.map(device => (
                    <DeviceCard 
                    key={device.id} 
                    device={device} 
                    latestTelemetry={telemetry[device.id]}
                    />
                ))}
                </div>
            </div>
        </div>
    );
};

export default Farm;