export class WebSocketClient {
    constructor() {
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
    }

    connectTelemetry(deviceId, onMessage, options = {}) {
        console.log("[WEBSOCKET.JS] Connecting to telemetry WS");
        const url = `ws://localhost:8000/api/v1/ws/telemetry/${deviceId}`;
        this.connect(url, onMessage, options);
    }

    connectVideo(deviceId, onMessage, options = {}) {
        console.log("[WEBSOCKET.JS] Connecting to Video WS");
        const url = `ws://localhost:8000/api/v1/ws/video/${deviceId}`;
        this.connect(url, onMessage, options);
    }

    connect(url, onMessage, options = {}) {
        try {
            this.ws = new WebSocket(url);

            this.ws.onopen = () => {
                console.log('>>> WebSocket connected');
                this.reconnectAttempts = 0;
                if (options.onOpen) options.onOpen();
                
                // Start ping/pong to keep connection alive
                this.pingInterval = setInterval(() => {
                    if (this.ws.readyState === WebSocket.OPEN) {
                        this.ws.send('ping');
                    }
                }, 30000);
            };

            this.ws.onmessage = (event) => {
                try {
                    if (event.data === 'pong') {
                        console.log("Received pong");
                        return;
                    } else if (event.data === 'ping') {
                        if (this.ws.readyState === WebSocket.OPEN) {
                            this.ws.send('pong');
                        }
                        return;
                    } 

                    const data = JSON.parse(event.data);
                    onMessage(data);
                } catch (e) {
                    console.error('Failed to parse WebSocket message:', e);
                }
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                if (options.onError) options.onError(error);
            };

            this.ws.onclose = () => {
                console.log('WebSocket disconnected');
                clearInterval(this.pingInterval);
                if (options.onClose) options.onClose();
                
                // Attempt to reconnect
                if (this.reconnectAttempts < this.maxReconnectAttempts) {
                    this.reconnectAttempts++;
                    setTimeout(() => {
                        this.connect(url, onMessage, options);
                    }, this.reconnectDelay * this.reconnectAttempts);
                }
            };
        } catch (error) {
            console.error('Failed to create WebSocket:', error);
            if (options.onError) options.onError(error);
        }
    }

    disconnect() {
        if (this.ws) {
            clearInterval(this.pingInterval);
            this.ws.close();
            this.ws = null;
        }
    }

    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        }
    }
}