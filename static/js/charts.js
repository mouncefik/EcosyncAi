/**
 * Charts JavaScript file for Energy Insight application
 * Uses Plotly.js for interactive visualizations
 */

/**
 * Creates a pie chart for consumption breakdown
 * 
 * @param {string} elementId - DOM element ID to render chart
 * @param {Array} labels - Array of device labels
 * @param {Array} values - Array of consumption values
 */
function createConsumptionPieChart(elementId, labels, values) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    const data = [{
        type: 'pie',
        labels: labels,
        values: values,
        textinfo: 'label+percent',
        insidetextorientation: 'radial',
        marker: {
            colors: [
                '#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', 
                '#e74a3b', '#858796', '#f8f9fc', '#5a5c69',
                '#6610f2'
            ]
        }
    }];
    
    const layout = {
        title: 'Consumption Breakdown',
        height: 400,
        margin: { t: 30, b: 0, l: 0, r: 0 },
        showlegend: true,
        legend: {
            orientation: 'h',
            y: -0.1
        },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)'
    };
    
    const config = {
        responsive: true,
        displayModeBar: false
    };
    
    Plotly.newPlot(elementId, data, layout, config);
}

/**
 * Creates a bar chart for generation forecast
 * 
 * @param {string} elementId - DOM element ID to render chart
 * @param {Array} dates - Array of date labels
 * @param {Array} values - Array of generation values
 */
function createGenerationBarChart(elementId, dates, values) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    const data = [{
        type: 'bar',
        x: dates,
        y: values,
        marker: {
            color: '#f6c23e'
        },
        hovertemplate: '%{y:.2f} kWh<extra></extra>'
    }];
    
    const layout = {
        title: 'Daily Generation Forecast',
        height: 400,
        margin: { t: 50, b: 50, l: 50, r: 30 },
        xaxis: {
            title: 'Date'
        },
        yaxis: {
            title: 'Energy (kWh)'
        },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)'
    };
    
    const config = {
        responsive: true,
        displayModeBar: false
    };
    
    Plotly.newPlot(elementId, data, layout, config);
}

/**
 * Creates a line chart for hourly generation profile
 * 
 * @param {string} elementId - DOM element ID to render chart
 * @param {Array} hourlyValues - Array of 24 hourly generation values
 */
function createHourlyLineChart(elementId, hourlyValues) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    const hours = Array.from({length: 24}, (_, i) => i);
    
    const data = [{
        type: 'scatter',
        mode: 'lines',
        x: hours,
        y: hourlyValues,
        line: {
            color: '#f6c23e',
            width: 3
        },
        fill: 'tozeroy',
        fillcolor: 'rgba(246, 194, 62, 0.2)',
        hovertemplate: '%{y:.2f} kWh<extra>Hour %{x}:00</extra>'
    }];
    
    const layout = {
        title: 'Hourly Generation Profile',
        height: 300,
        margin: { t: 50, b: 50, l: 50, r: 30 },
        xaxis: {
            title: 'Hour of Day',
            tickvals: [0, 4, 8, 12, 16, 20, 23],
            ticktext: ['12 AM', '4 AM', '8 AM', '12 PM', '4 PM', '8 PM', '11 PM']
        },
        yaxis: {
            title: 'Energy (kWh)'
        },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)'
    };
    
    const config = {
        responsive: true,
        displayModeBar: false
    };
    
    Plotly.newPlot(elementId, data, layout, config);
}

/**
 * Creates a combined line chart for hourly profiles (generation, consumption, optimized)
 * 
 * @param {string} elementId - DOM element ID to render chart
 * @param {Array} generation - Array of 24 hourly generation values
 * @param {Array} consumption - Array of 24 hourly consumption values
 * @param {Array} optimized - Array of 24 hourly optimized consumption values
 */
function createHourlyProfileChart(elementId, generation, consumption, optimized) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    const hours = Array.from({length: 24}, (_, i) => i);
    
    const data = [
        {
            type: 'scatter',
            mode: 'lines',
            name: 'Solar Generation',
            x: hours,
            y: generation,
            line: {
                color: '#f6c23e',
                width: 3
            },
            fill: 'tozeroy',
            fillcolor: 'rgba(246, 194, 62, 0.1)',
            hovertemplate: '%{y:.2f} kWh<extra>Hour %{x}:00</extra>'
        },
        {
            type: 'scatter',
            mode: 'lines',
            name: 'Original Consumption',
            x: hours,
            y: consumption,
            line: {
                color: '#e74a3b',
                width: 3
            },
            hovertemplate: '%{y:.2f} kWh<extra>Hour %{x}:00</extra>'
        },
        {
            type: 'scatter',
            mode: 'lines',
            name: 'Optimized Consumption',
            x: hours,
            y: optimized,
            line: {
                color: '#1cc88a',
                width: 3,
                dash: 'dash'
            },
            hovertemplate: '%{y:.2f} kWh<extra>Hour %{x}:00</extra>'
        }
    ];
    
    const layout = {
        title: 'Hourly Energy Profile',
        height: 400,
        margin: { t: 50, b: 50, l: 50, r: 30 },
        xaxis: {
            title: 'Hour of Day',
            tickvals: [0, 4, 8, 12, 16, 20, 23],
            ticktext: ['12 AM', '4 AM', '8 AM', '12 PM', '4 PM', '8 PM', '11 PM']
        },
        yaxis: {
            title: 'Energy (kWh)'
        },
        legend: {
            orientation: 'h',
            y: 1.1
        },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)'
    };
    
    const config = {
        responsive: true,
        displayModeBar: false
    };
    
    Plotly.newPlot(elementId, data, layout, config);
}
