import { h } from 'preact';
import { useEffect, useRef, useState } from 'preact/hooks';
import { WebSocketClient } from '../services/websocket';

const VideoStream = ({ deviceId, onClose }) => {
    const [connected, setConnected] = useState(false);
    const [frameCount, setFrameCount] = useState(0);
    const videoRef = useRef(null);
    const wsRef = useRef(null);

    useEffect(() => {
        const ws = new WebSocketClient();
        wsRef.current = ws;

        ws.connectVideo(deviceId, (data) => {
            // TODO In production, this would handle actual video frames
            // For now, just update frame count
            if (data.type === 'frame') {
                setFrameCount(data.frame);
            }
        }, {
            onOpen: () => setConnected(true),
            onClose: () => setConnected(false)
        });

        return () => {
            if (wsRef.current) {
                wsRef.current.disconnect();
            }
        };
    }, [deviceId]);

    return (
        <div className="relative bg-black rounded-lg overflow-hidden">
            <div className="aspect-w-16 aspect-h-9" style={{ paddingBottom: '56.25%' }}>
                <div className="absolute inset-0 flex items-center justify-center">
                    {/* In production, this would be a video element or canvas */}
                    <div className="text-white text-center">
                        <div className="text-4xl font-mono mb-2">
                            Frame: {frameCount}
                        </div>
                        <div className="text-sm">
                            {connected ? (
                                <span className="text-green-400">● Connected</span>
                            ) : (
                                <span className="text-red-400">● Disconnected</span>
                            )}
                        </div>
                    </div>
                </div>
            </div>
            
            <button
                onClick={onClose}
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