import { h } from 'preact';
import { useEffect, useRef } from 'preact/hooks';

const MetricChart = ({ data, metric, title }) => {
    const canvasRef = useRef(null);

    useEffect(() => {
        if (!canvasRef.current || !data.length) return;

        const canvas = canvasRef.current;
        const ctx = canvas.getContext('2d');
        const width = canvas.width = canvas.offsetWidth;
        const height = canvas.height = 200;

        // Clear canvas
        ctx.clearRect(0, 0, width, height);

        // Extract values
        const values = data.map(d => d[metric]);
        const timestamps = data.map(d => new Date(d.timestamp));
        
        if (values.length === 0) return;

        const minValue = Math.min(...values);
        const maxValue = Math.max(...values);
        const valueRange = maxValue - minValue || 1;
        
        // Drawing settings
        const padding = 40;
        const graphWidth = width - 2 * padding;
        const graphHeight = height - 2 * padding;

        // Draw axes
        ctx.strokeStyle = '#e5e7eb';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(padding, padding);
        ctx.lineTo(padding, height - padding);
        ctx.lineTo(width - padding, height - padding);
        ctx.stroke();

        // Draw grid lines
        ctx.strokeStyle = '#f3f4f6';
        for (let i = 0; i <= 5; i++) {
            const y = padding + (graphHeight * i) / 5;
            ctx.beginPath();
            ctx.moveTo(padding, y);
            ctx.lineTo(width - padding, y);
            ctx.stroke();
            
            // Y-axis labels
            const value = maxValue - (valueRange * i) / 5;
            ctx.fillStyle = '#6b7280';
            ctx.font = '10px sans-serif';
            ctx.textAlign = 'right';
            ctx.fillText(value.toFixed(1), padding - 5, y + 3);
        }

        // Draw the line chart
        ctx.strokeStyle = '#10b981';
        ctx.lineWidth = 2;
        ctx.beginPath();
        
        values.forEach((value, index) => {
            const x = padding + (graphWidth * index) / (values.length - 1);
            const y = padding + graphHeight - ((value - minValue) / valueRange) * graphHeight;
            
            if (index === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
            
            // Draw point
            ctx.fillStyle = '#10b981';
            ctx.beginPath();
            ctx.arc(x, y, 3, 0, 2 * Math.PI);
            ctx.fill();
        });
        
        ctx.stroke();

        // Draw time labels
        ctx.fillStyle = '#6b7280';
        ctx.font = '10px sans-serif';
        ctx.textAlign = 'center';
        
        const labelCount = Math.min(5, timestamps.length);
        const step = Math.floor((timestamps.length - 1) / (labelCount - 1));
        
        for (let i = 0; i < labelCount; i++) {
            const index = i * step;
            const x = padding + (graphWidth * index) / (values.length - 1);
            const time = timestamps[index];
            const label = time.getHours().toString().padStart(2, '0') + ':' + 
                        time.getMinutes().toString().padStart(2, '0');
            ctx.fillText(label, x, height - padding + 15);
        }

        // Title
        ctx.fillStyle = '#111827';
        ctx.font = 'bold 12px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(title, width / 2, 15);

    }, [data, metric, title]);

    return (
        <div className="w-full">
            <canvas 
                ref={canvasRef} 
                className="w-full"
                style={{ maxHeight: '200px' }}
            />
        </div>
    );
};

export default MetricChart;