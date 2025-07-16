import { h } from 'preact';
import { useState, useEffect } from 'preact/hooks';
import FarmCard from '../components/FarmCard';
import { apiClient } from '../services/api';

const Landing = () => {
    const [farms, setFarms] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetchFarms();
    }, []);

    const fetchFarms = async () => {
        try {
            const data = await apiClient.getFarms();
            setFarms(data);
        } catch (err) {
            setError('Failed to load farms');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

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
            <div className="mb-6">
                <h2 className="text-2xl font-bold text-gray-900">Farms</h2>
                <p className="text-gray-600 mt-1">Monitor and manage your plant farms</p>
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
