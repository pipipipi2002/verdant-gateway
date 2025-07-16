import { h } from 'preact';

const Layout = ({ children, connectionStatus }) => {
    const getStatusColor = () => {
        switch (connectionStatus) {
            case 'local': return 'bg-green-500';
            case 'remote': return 'bg-yellow-500';
            case 'offline': return 'bg-red-500';
            default: return 'bg-gray-500';
        }
    };

    return (
        <div className="min-h-screen bg-gray-100">
            <header className="bg-white shadow-sm">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex justify-between items-center h-16">
                    <h1 className="text-xl font-semibold text-gray-900">
                        Plant Monitoring System
                    </h1>
                    <div className="flex items-center space-x-2">
                        <span className="text-sm text-gray-600">Connection:</span>
                            <div className={`px-3 py-1 rounded-full text-white text-xs ${getStatusColor()}`}>
                                {connectionStatus.toUpperCase()}
                            </div>
                        </div>
                    </div>
                </div>
            </header>
            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {children}
            </main>
        </div>
    );
};

export default Layout