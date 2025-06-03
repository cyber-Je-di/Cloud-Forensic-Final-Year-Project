import { Chart } from "@/components/ui/chart"
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
  // Alert Statistics Chart
  const threatCtx = document.getElementById("threatChart").getContext("2d")
  const threatChart = new Chart(threatCtx, {
    type: "line",
    data: {
      labels: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul"],
      datasets: [
        {
          label: "Critical Alerts",
          data: [65, 59, 80, 81, 56, 55, 40],
          borderColor: "#f72585",
          backgroundColor: "rgba(247, 37, 133, 0.1)",
          tension: 0.4,
          fill: true,
        },
        {
          label: "Warning Alerts",
          data: [28, 48, 40, 19, 86, 27, 90],
          borderColor: "#4cc9f0",
          backgroundColor: "rgba(76, 201, 240, 0.1)",
          tension: 0.4,
          fill: true,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "top",
        },
        title: {
          display: false,
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          grid: {
            color: "rgba(0, 0, 0, 0.05)",
          },
        },
        x: {
          grid: {
            display: false,
          },
        },
      },
    },
  })

  // Logs Per Tenant Chart
  const logsCtx = document.getElementById("logsPerTenantChart").getContext("2d")
  const logsChart = new Chart(logsCtx, {
    type: "doughnut",
    data: {
      labels: ["Tenant A", "Tenant B", "Tenant C", "Tenant D", "Others"],
      datasets: [
        {
          data: [35, 25, 20, 15, 5],
          backgroundColor: ["#4361ee", "#3a0ca3", "#4895ef", "#4cc9f0", "#f72585"],
          borderWidth: 0,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "right",
        },
      },
      cutout: "65%",
    },
  })
}
