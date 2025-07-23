import { h } from 'preact';
import { useState, useEffect } from 'preact/hooks';
import FarmCard from '../components/FarmCard';
import { apiClient } from '../services/api';

const Landing = () => {
    const [farms, setFarms] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [lastUpdated, setLastUpdated] = useState(null);

    useEffect(() => {
        fetchFarms();
    }, []);

    const fetchFarms = async () => {
        try {
            setLoading(true);
            setError(null);
      
            const data = await apiClient.getFarms();
            setFarms(data);
            setLastUpdated(new Date());
        } catch (err) {
            setError('Failed to load farms');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleRefresh = () => {
        fetchFarms();
    }

    if (loading) {
        return (
            <div className="flex justify-center items-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-500"></div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="text-center py-12">
                <p className="text-red-600">{error}</p>
                <button
                onClick={fetchFarms}
                className="mt-4 px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
                >
                    Retry
                </button>
            </div>
        );
    }

    return (
        <div>
            <div className="mb-6 flex justify-between items-center">
                <div>
                    <h2 className="text-2xl font-bold text-gray-900">Farms</h2>
                    <p className="text-gray-600 mt-1">Monitor and manage your plant farms</p>
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

            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                {farms.map(farm => (
                <FarmCard key={farm.id} farm={farm} />
                ))}
            </div>

            {farms.length === 0 && (
                <div className="text-center py-12">
                    <p className="text-gray-500">No farms configured</p>
                </div>
            )}
        </div>
    );
};

export default Landing;
