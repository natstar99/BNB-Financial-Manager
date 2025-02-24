// File: views/analysis_plot.js

/**
 * Component for rendering financial category plots
 * @param {Object} props Component properties
 * @param {Array} props.data The data to plot
 * @param {string} props.plotType Type of plot ('line' or 'column')
 * @param {string} props.valueType Type of value to display
 * @param {string} props.displayMode Display mode ('independent' or 'combined')
 * @param {boolean} props.showAverage Whether to show average line
 * @param {Array} props.categories List of categories to plot
 */


// analysis_plot.js
const CategoryPlot = ({ data, plotType, valueType, displayMode, showAverage, categories }) => {
  const {
    LineChart, Line, BarChart, Bar, XAxis, YAxis,
    CartesianGrid, Tooltip, Legend, ReferenceLine,
    ResponsiveContainer
  } = Recharts;

  // Error boundary
  if (!data || !Array.isArray(data) || data.length === 0) {
    return React.createElement('div', {
      className: 'error-message',
      style: {
        padding: '20px',
        textAlign: 'center',
        color: '#666'
      }
    }, 'No data available for plotting');
  }

  // Format tooltip values with Australian dollar format
  const formatValue = (value) => new Intl.NumberFormat('en-AU', {
    style: 'currency',
    currency: 'AUD'
  }).format(value);

  // Calculate domain for Y axis
  const getAllValues = () => {
    const values = [];
    data.forEach(item => {
      if (displayMode === 'independent') {
        Object.values(item.values || {}).forEach(v => values.push(v));
      } else {
        values.push(item.combinedValue);
      }
    });
    return values;
  };

  const values = getAllValues();
  const maxAbs = Math.max(Math.abs(Math.min(...values)), Math.abs(Math.max(...values)));
  const domain = [-maxAbs, maxAbs];

  // Common props for both chart types
  const commonProps = {
    width: '100%',
    height: 400,
    data,
    margin: { top: 20, right: 30, left: 50, bottom: 20 }
  };

  // Common axis props
  const commonAxisProps = {
    YAxis: {
      domain,
      tickFormatter: formatValue
    }
  };

  // Calculate average if needed
  const average = showAverage && plotType === 'column' ?
    data.reduce((sum, item) => {
      if (displayMode === 'independent') {
        return sum + Object.values(item.values || {}).reduce((a, b) => a + b, 0);
      }
      return sum + (item.combinedValue || 0);
    }, 0) / data.length : null;

  // Render appropriate chart type
  if (plotType === 'line') {
    return React.createElement(ResponsiveContainer, { width: '100%', height: 400 },
      React.createElement(LineChart, commonProps,
        React.createElement(CartesianGrid, { strokeDasharray: '3 3' }),
        React.createElement(XAxis, { dataKey: 'date' }),
        React.createElement(YAxis, commonAxisProps.YAxis),
        React.createElement(Tooltip, {
          formatter: formatValue,
          labelFormatter: (label) => `Period: ${label}`
        }),
        React.createElement(Legend, { verticalAlign: 'top', height: 36 }),
        React.createElement(ReferenceLine, { y: 0, stroke: '#666', strokeDasharray: '3 3' }),
        displayMode === 'independent' ?
          categories.map((category, index) =>
            React.createElement(Line, {
              key: category.id,
              type: 'monotone',
              dataKey: `values.${category.id}`,
              name: category.name,
              stroke: `hsl(${(index * 137.5) % 360}, 70%, 50%)`,
              strokeWidth: 2,
              dot: false,
              activeDot: { r: 4 }
            })
          ) :
          React.createElement(Line, {
            type: 'monotone',
            dataKey: 'combinedValue',
            name: 'Combined',
            stroke: '#8884d8',
            strokeWidth: 2,
            dot: false,
            activeDot: { r: 4 }
          })
      )
    );
  }

  return React.createElement(ResponsiveContainer, { width: '100%', height: 400 },
    React.createElement(BarChart, commonProps,
      React.createElement(CartesianGrid, { strokeDasharray: '3 3' }),
      React.createElement(XAxis, { dataKey: 'date' }),
      React.createElement(YAxis, commonAxisProps.YAxis),
      React.createElement(Tooltip, {
        formatter: formatValue,
        labelFormatter: (label) => `Period: ${label}`
      }),
      React.createElement(Legend, { verticalAlign: 'top', height: 36 }),
      React.createElement(ReferenceLine, { y: 0, stroke: '#666', strokeDasharray: '3 3' }),
      displayMode === 'independent' ?
        categories.map((category, index) =>
          React.createElement(Bar, {
            key: category.id,
            dataKey: `values.${category.id}`,
            name: category.name,
            fill: `hsl(${(index * 137.5) % 360}, 70%, 50%)`
          })
        ) :
        React.createElement(Bar, {
          dataKey: 'combinedValue',
          name: 'Combined',
          fill: '#8884d8'
        }),
      showAverage && React.createElement(ReferenceLine, {
        y: average,
        stroke: '#666',
        strokeDasharray: '3 3',
        label: {
          value: `Avg: ${formatValue(average)}`,
          position: 'right'
        }
      })
    )
  );
};

// Make the component available globally
window.CategoryPlot = CategoryPlot;