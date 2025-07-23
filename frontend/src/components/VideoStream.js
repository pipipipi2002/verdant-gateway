import { h,  Fragment} from 'preact';
import { useEffect, useRef, useState } from 'preact/hooks';


const VideoStream = ({ deviceId, onClose }) => {
    const [connected, setConnected] = useState(false);
    const [frameCount, setFrameCount] = useState(0);
    const [error, setError] = useState(null);
    const wsRef = useRef(null);

    useEffect(() => {
        let ws = null;
        let reconnectTimeout = null;
        let isMounted = true;

        const connect = () => {
            if (!isMounted) return;

            try {
                const wsUrl = `ws://localhost:8000/api/v1/ws/video/${deviceId}`;
                ws = new WebSocket(wsUrl);

                ws.onopen = () => {
                    console.log('Video WebSocket connected');
                    if (isMounted) {
                        setConnected(true);
                        setError(null);
                    }
                };

                ws.onmessage = (event) => {
                    try {
                        const data = JSON.parse(event.data);
                        if (data.type === 'frame' && isMounted) {
                            setFrameCount(data.frame);
                        }
                    } catch (e) {
                        console.error('Failed to parse video frame: ', e);
                    }
                };

                ws.onerror = (error) => {
                    console.error('Video WebSocket error:', error);
                    if (isMounted) {
                        setError('Connection error');
                    }
                };

                wsRef.current = ws;
            } catch(error) {
                console.error('Failed to create Websocket:', error);
                if (isMounted) {
                    setError('Failed to connect');
                    reconnectTimeout = setTimeout(connect, 2000);
                }
            }
        };

        console.log('Connecting to Video WebSocket');
        connect();

        return () => {
            isMounted = false;
            if (reconnectTimeout) {
                clearTimeout(reconnectTimeout);
            }

            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.close(1000, 'Component Unmounting');
            }
        };
    }, [deviceId]);

    const handleClose = () => {
        console.log('Closing stream');
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            wsRef.current.close(1000, 'User closed');
        }

        // Give timeout to properly close ws
        setTimeout(() => {
            onClose();
        }, 100);
    };

    return (
        <div className="relative bg-black rounded-lg overflow-hidden">
            <div className="aspect-w-16 aspect-h-9" style={{ paddingBottom: '56.25%' }}>
                <div className="absolute inset-0 flex items-center justify-center">
                    {/* In production, this would be a video element or canvas */}
                    <div className="text-white text-center">
                        {error ? (
                            <div className="text-red-400">
                                <p className="text-lg mb-2">{error}</p>
                                <p className="text-sm">Check console for details</p>
                            </div>
                        ) : (
                            <>
                            <div className="text-4xl font-mono mb-2">
                                Frame: {frameCount}
                            </div>
                            <div className="text-sm">
                                {connected ? (
                                    <span className="text-green-400">● Connected</span>
                                ) : (
                                    <span className="text-yellow-400">● Connecting...</span>
                                )}
                            </div>
                            </>
                        )}
                    </div>
                </div>
            </div>
        
            <button
                onClick={handleClose}
                className="absolute top-2 right-2 p-2 bg-red-500 text-white rounded hover:bg-red-600"
            >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
            </button>
        </div>
    );
};

export default VideoStream;