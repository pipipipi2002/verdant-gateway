import { h } from 'preact';
import { useState } from 'preact/hooks';
import { route } from 'preact-router';

const FarmCard = ({ farm }) => {
    const [expanded, setExpanded] = useState(false);

    const handleCardClick = (e) => {
        e.stopPropagation();
        setExpanded(!expanded);
    };

    const handleNavigate = (e) => {
        e.stopPropagation();
        route(`/farm/${farm.id}`);
    };

    return (
        <div 
            className="bg-white rounded-lg shadow hover:shadow-md transition-shadow cursor-pointer"
            onClick={handleCardClick}
        >
            <div className="p-6">
                <div className="flex justify-between items-start">
                    <div className="flex-1">
                        <h3 className="text-lg font-semibold text-gray-900">{farm.name}</h3>
                        <p className="text-sm text-gray-600 mt-1">{farm.location}</p>
                    
                        <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
                            <div>
                                <span className="text-gray-500">Total Devices:</span>
                                <p className="font-medium">{farm.device_count}</p>
                            </div>
                            <div>
                                <span className="text-gray-500">Active:</span>
                                <p className="font-medium text-green-600">{farm.active_devices}</p>
                            </div>
                        </div>
                    
                        {/* Connection Status Tag */}
                        <div className="mt-3">
                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium
                                ${farm.connection_status === 'local' ? 'bg-green-100 text-green-800' : 
                                farm.connection_status === 'remote' ? 'bg-yellow-100 text-yellow-800' : 
                                'bg-red-100 text-red-800'}`}>
                                {farm.connection_status}
                            </span>
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
                
                {/* Expandable Content */}
                {expanded && (
                    <div className="mt-4 pt-4 border-t border-gray-200">
                        <div className="grid grid-cols-2 gap-4 text-sm">
                            <div>
                                <span className="text-gray-500">Offline Devices:</span>
                                <p className="font-medium text-red-600">{farm.offline_devices}</p>
                            </div>
                            <div>
                                <span className="text-gray-500">Gateway ID:</span>
                                <p className="font-medium">{farm.gateway_id}</p>
                            </div>
                            <div className="col-span-2">
                                <span className="text-gray-500">Last Updated:</span>
                                <p className="font-medium">{new Date(farm.updated_at).toLocaleString()}</p>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default FarmCard
