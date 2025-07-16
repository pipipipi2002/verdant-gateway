# Plant Monitoring System

A comprehensive IoT solution for monitoring plant health in agricultural settings. This system consists of a local gateway (Bateway Node) that collects data from various sensors and provides real-time monitoring through a web interface.

## Architecture Overview

- **Backend**: FastAPI (Python) - High-performance async API server
- **Frontend**: Preact - Lightweight React alternative optimized for edge devices
- **Real-time Communication**: WebSocket for live telemetry and video streaming
- **Data Flow**: MQTT → HTTP Bridge → WebSocket → Web UI

## Features

### Current MVP Features

- ✅ Farm and device management
- ✅ Real-time telemetry display (soil humidity, temperature, CO2, etc.)
- ✅ WebSocket-based live data streaming
- ✅ Device configuration and control
- ✅ Gateway health monitoring
- ✅ Responsive web interface
- ✅ Expandable card UI for progressive disclosure
- ✅ Historical data visualization with charts

### Planned Features

- 🔄 TimescaleDB integration for time-series data
- 🔄 MQTT broker integration for device communication
- 🔄 Security layer with JWT authentication
- 🔄 Data synchronization with cloud server
- 🔄 Automated backup and recovery
- 🔄 Device provisioning workflow

## Project Structure

```
plant-monitoring-system/
├── backend/
│   ├── app/
│   │   ├── api/v1/       # API endpoints
│   │   ├── models/       # Data models
│   │   ├── services/     # Business logic
│   │   └── utils/        # Utilities
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/   # Reusable components
│   │   ├── pages/        # Page components
│   │   ├── services/     # API and WebSocket clients
│   │   └── styles/       # CSS files
│   └── package.json
└── README.md
```

## Installation

### Prerequisites

- Python 3.8+
- Node.js 14+
- npm or yarn

### Backend Setup

1. Navigate to the backend directory:

```bash
cd backend
```

2. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Run the server:

```bash
python run.py
```

The backend will start on `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:

```bash
cd frontend
```

2. Install dependencies:

```bash
npm install
```

3. Start the development server:

```bash
npm start
```

The frontend will start on `http://localhost:3000`

## Usage

### Accessing the System

1. Open your browser and navigate to `http://localhost:3000`
2. The landing page shows all configured farms
3. Click on a farm card to expand details or navigate to the farm page
4. From the farm page, view all devices and their status
5. Click on a device to see detailed telemetry and controls

### API Documentation

Once the backend is running, access the interactive API documentation at:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### WebSocket Endpoints

- Telemetry: `ws://localhost:8000/api/v1/ws/telemetry/{device_id}`
- Video Stream: `ws://localhost:8000/api/v1/ws/video/{device_id}`

## Development

### Adding New Metrics

1. Update the `TelemetryData` model in `backend/app/models/telemetry.py`
2. Modify the telemetry display in `frontend/src/pages/Device.js`
3. Add the metric to the chart options in `MetricChart.js`

### Integrating Real Devices

1. **MQTT Integration**:

   - Uncomment `paho-mqtt` in `requirements.txt`
   - Implement actual MQTT client in `mqtt_bridge.py`
   - Update topic structure to match your devices

2. **Database Integration**:

   - Install TimescaleDB
   - Update `data_store.py` to use actual database
   - Implement data retention policies

3. **Camera Integration**:
   - Implement actual video streaming in WebSocket endpoints
   - Update `VideoStream.js` to handle real video frames

### Production Deployment

1. **Security**:

   - Enable HTTPS/WSS
   - Implement JWT authentication
   - Set proper CORS origins

2. **Performance**:

   - Use production builds: `npm run build`
   - Enable caching
   - Implement connection pooling

3. **Monitoring**:
   - Set up logging aggregation
   - Implement alerting
   - Monitor resource usage

## API Examples

### Get All Devices

```bash
curl http://localhost:8000/api/v1/devices
```

### Update Device Configuration

```bash
curl -X PATCH http://localhost:8000/api/v1/devices/device-001/config \
  -H "Content-Type: application/json" \
  -d '{"telemetry_interval": 30, "snapshot_interval": 1800}'
```

### Send Device Command

```bash
curl -X POST http://localhost:8000/api/v1/devices/device-001/command \
  -H "Content-Type: application/json" \
  -d '{"command": "capture_snapshot"}'
```

## Troubleshooting

### Backend Issues

- Ensure Python 3.8+ is installed
- Check that all ports (8000, 1883) are available
- Verify virtual environment is activated

### Frontend Issues

- Clear browser cache if UI doesn't update
- Check browser console for errors
- Ensure backend is running before starting frontend

### WebSocket Connection Issues

- Check that WebSocket URLs use correct protocol (ws:// not http://)
- Verify device IDs exist in the system
- Check browser developer tools for connection errors

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Future Enhancements

- **Multi-tenant support**: Support multiple organizations
- **Mobile app**: React Native companion app
- **AI Integration**: Predictive analytics for plant health
- **Alerts**: Configurable thresholds and notifications
- **Export functionality**: CSV/PDF reports
- **3D visualization**: Plant growth tracking
- **Weather integration**: Correlate with local weather data
