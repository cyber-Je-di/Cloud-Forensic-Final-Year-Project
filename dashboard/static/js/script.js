// Remove the import line. Chart is global after loading the CDN.
// import { Chart } from "@/components/ui/chart";
document.addEventListener("DOMContentLoaded", () => {
  // …
  const threatCtx = document.getElementById("threatChart").getContext("2d");
  const threatChart = new Chart(threatCtx, { … }); // Chart is global
  // …
});

// Toggle sidebar
document.addEventListener("DOMContentLoaded", () => {
  const sidebarToggle = document.getElementById("sidebarToggle")
  const sidebar = document.querySelector(".sidebar")

  sidebarToggle.addEventListener("click", () => {
    sidebar.classList.toggle("collapsed")
  })

  // Initialize charts
  initCharts()
})

function initCharts() {
    // Alert Statistics Chart (threatChart)
    const threatCtx = document.getElementById("threatChart").getContext("2d");

    const defaultSeverityOrder = ["Critical", "High", "Medium", "Low", "Unknown"];
    let alertLabels = [];
    let alertDataPoints = [];

    if (typeof alertSeverityData === 'object' && alertSeverityData !== null && Object.keys(alertSeverityData).length > 0) {
        defaultSeverityOrder.forEach(severity => {
            if (alertSeverityData.hasOwnProperty(severity)) {
                alertLabels.push(severity);
                alertDataPoints.push(alertSeverityData[severity]);
            } else {
                // Optionally include severities with 0 count if they are in defaultSeverityOrder
                // For a cleaner bar chart, we might only show severities that are present or have counts > 0
                // If you want all severities from defaultSeverityOrder to always appear:
                // alertLabels.push(severity);
                // alertDataPoints.push(0);
            }
        });
        // If after checking, no data points were added (e.g. all severities were 0 and we skipped them)
        if (alertLabels.length === 0) {
             alertLabels = ['No alert data']; // Default labels for empty chart
             alertDataPoints = [0]; // Default data for empty chart
        }
    } else {
        console.error("alertSeverityData is not available, not an object, or is empty:", alertSeverityData);
        alertLabels = ['Alert data not available']; // Fallback labels
        alertDataPoints = [0]; // Fallback data
    }

    const threatChart = new Chart(threatCtx, {
        type: "bar",
        data: {
            labels: alertLabels,
            datasets: [{
                label: "Current Alert Counts",
                data: alertDataPoints,
                backgroundColor: 'rgba(247, 37, 133, 0.6)',
                borderColor: 'rgba(247, 37, 133, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: "top",
                    display: alertDataPoints.length > 0 && alertDataPoints.some(d => d > 0) && alertLabels[0] !== 'No alert data' && alertLabels[0] !== 'Alert data not available'
                },
                title: { display: false }
            },
            scales: {
                y: { beginAtZero: true, grid: { color: "rgba(0, 0, 0, 0.05)" } },
                x: { grid: { display: false } }
            }
        }
    });

    // Logs Per Tenant Chart (logsPerTenantChart)
    const logsCtx = document.getElementById("logsPerTenantChart").getContext("2d");

    let logLabels = [];
    let logDataPoints = [];
    // Extended palette for more tenants
    const backgroundColors = [
        "#4361ee", "#3a0ca3", "#4895ef", "#4cc9f0", "#f72585",
        "#ff9f1c", "#00f5d4", "#9b5de5", "#f15bb5", "#fee440",
        "#00bbf9", "#00f5d4", "#f3722c", "#f8961e", "#f9c74f",
        "#90be6d", "#43aa8b", "#577590"
    ];


    if (typeof logsPerTenantChartData === 'object' && logsPerTenantChartData !== null && Object.keys(logsPerTenantChartData).length > 0) {
        logLabels = Object.keys(logsPerTenantChartData);
        logDataPoints = Object.values(logsPerTenantChartData);
    } else {
        console.error("logsPerTenantChartData is not available, not an object, or is empty:", logsPerTenantChartData);
        logLabels = ['No log data']; // Fallback label
        logDataPoints = [1]; // Doughnut chart needs a value to render placeholder circle
    }

    const logsChart = new Chart(logsCtx, {
        type: "doughnut",
        data: {
            labels: logLabels,
            datasets: [{
                data: logDataPoints,
                backgroundColor: backgroundColors.slice(0, logDataPoints.length > 0 ? logDataPoints.length : 1),
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: "right",
                    display: logDataPoints.length > 0 && logLabels[0] !== 'No log data' && logDataPoints.some(d => d > 0)
                }
            },
            cutout: "65%"
        }
    });
}
