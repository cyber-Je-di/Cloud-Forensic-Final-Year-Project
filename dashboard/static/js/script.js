const threatData = {{ stats | tojson }};
const logsPerTenant = {{ logs_per_tenant | tojson }};

// Threat Type Bar Chart
new Chart(document.getElementById('threatChart'), {
  type: 'bar',
  data: {
    labels: Object.keys(threatData),
    datasets: [{
      label: 'Threat Counts',
      data: Object.values(threatData),
      backgroundColor: 'rgba(255, 99, 132, 0.7)'
    }]
  },
  options: {
    responsive: true,
    plugins: {
      legend: { display: false },
      title: { display: true, text: 'Threat Types Detected' }
    }
  }
});

// Logs Per Tenant Line Chart
new Chart(document.getElementById('logsPerTenantChart'), {
  type: 'line',
  data: {
    labels: Object.keys(logsPerTenant),
    datasets: [{
      label: 'Log Entries',
      data: Object.values(logsPerTenant),
      fill: false,
      borderColor: 'rgba(54, 162, 235, 0.7)',
      tension: 0.1
    }]
  },
  options: {
    responsive: true,
    plugins: {
      title: { display: true, text: 'Logs per Tenant' }
    }
  }
});