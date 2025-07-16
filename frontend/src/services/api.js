const API_BASE_URL = 'http://localhost:8000/api/v1';

class ApiClient {
    async request(url, options = {}) {
        const response = await fetch(`${API_BASE_URL}${url}`, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
        });

        if (!response.ok) {
            throw new Error(`API Error: ${response.status} ${response.statusText}`);
        }

        return response.json();
    }

    // Farms
    async getFarms() {
        return this.request('/farms');
    }

    async getFarmDetail(farmId) {
        return this.request(`/farms/${farmId}`);
    }

    // Devices
    async getDevices(farmId) {
        const query = farmId ? `?farm_id=${farmId}` : '';
        return this.request(`/devices${query}`);
    }

    async getDeviceDetail(deviceId) {
        return this.request(`/devices/${deviceId}`);
    }

    async updateDeviceConfig(deviceId, config) {
            return this.request(`/devices/${deviceId}/config`, {
            method: 'PATCH',
            body: JSON.stringify(config),
        });
    }

    async sendCommand(deviceId, command) {
            return this.request(`/devices/${deviceId}/command`, {
            method: 'POST',
            body: JSON.stringify(command),
        });
    }

    // Telemetry
    async getTelemetryHistory(deviceId, hours = 24) {
        return this.request(`/telemetry/${deviceId}?hours=${hours}`);
    }

    async getLatestTelemetry(deviceId) {
        return this.request(`/telemetry/${deviceId}/latest`);
    }
}

export const apiClient = new ApiClient();