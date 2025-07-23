import { h, render } from 'preact';
import { Router } from 'preact-router';
import { useState, useEffect } from 'preact/hooks';

import Layout from './components/Layout';
import Landing from './pages/Landing';
import Farm from './pages/Farm';
import Device from './pages/Device';

const App = () => {
    const [connectionStatus, setConnectionStatus] = useState('checking');

    useEffect(() => {
        // Check connection status
        checkConnection();
        const interval = setInterval(checkConnection, 30000);

        return () => clearInterval(interval);
    }, []);

    const checkConnection = async () => {
        try {
            // This pings the backend for response.
            const response = await fetch('http://localhost:8000/health', {
                method: 'GET',
                mode: 'cors',
                cache: 'no-cache',
            });

            if (response.ok) {
                setConnectionStatus('local');
            } else {
                setConnectionStatus('offline');
            }
        } catch (error) {
            setConnectionStatus('offline');
        }
    };

    return (
        <Layout connectionStatus={connectionStatus}>
            <Router>
                <Landing path="/" />
                <Farm path="/farm/:farmId" />
                <Device path="/device/:deviceId" />
            </Router>
        </Layout>
    );
}

export default App;