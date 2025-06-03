document.addEventListener("DOMContentLoaded", () => {
  const tenantCards = document.querySelectorAll(".tenant-card")
  const tenantSelect = document.getElementById("tenantSelect")
  const continueBtn = document.getElementById("continueBtn")
  const clearBtn = document.getElementById("clearBtn")
  const selectedPreview = document.getElementById("selectedPreview")
  const previewName = document.getElementById("previewName")
  const form = document.getElementById("tenantForm")

  let selectedTenant = null

  // Initialize
  setupTenantSelection()
  setupFormSubmission()

  function setupTenantSelection() {
    tenantCards.forEach((card) => {
      card.addEventListener("click", () => {
        const tenantName = card.dataset.tenant

        // Remove previous selection
        tenantCards.forEach((c) => c.classList.remove("selected"))

        // Select current card
        card.classList.add("selected")
        selectedTenant = tenantName

        // Update form
        tenantSelect.value = tenantName
        updateUI()

        // Show selection with animation
        showSelectedPreview(tenantName)
      })

      // Add hover effects
      card.addEventListener("mouseenter", () => {
        if (!card.classList.contains("selected")) {
          card.style.transform = "translateY(-4px)"
        }
      })

      card.addEventListener("mouseleave", () => {
        if (!card.classList.contains("selected")) {
          card.style.transform = "translateY(0)"
        }
      })
    })

    // Clear selection
    clearBtn.addEventListener("click", () => {
      clearSelection()
    })
  }

  function showSelectedPreview(tenantName) {
    previewName.textContent = tenantName
    selectedPreview.style.display = "block"

    // Trigger animation
    setTimeout(() => {
      selectedPreview.classList.add("visible")
    }, 10)
  }

  function clearSelection() {
    // Remove selection from cards
    tenantCards.forEach((card) => {
      card.classList.remove("selected")
      card.style.transform = "translateY(0)"
    })

    // Reset form
    selectedTenant = null
    tenantSelect.value = ""

    // Hide preview
    selectedPreview.style.display = "none"
    selectedPreview.classList.remove("visible")

    updateUI()
  }

  function updateUI() {
    const hasSelection = selectedTenant !== null

    // Update continue button
    continueBtn.disabled = !hasSelection
    if (hasSelection) {
      continueBtn.classList.add("enabled")
    } else {
      continueBtn.classList.remove("enabled")
    }

    // Update clear button
    clearBtn.style.display = hasSelection ? "inline-flex" : "none"
  }

  function setupFormSubmission() {
    form.addEventListener("submit", (e) => {
      e.preventDefault()

      if (!selectedTenant) {
        showNotification("Please select a tenant to continue", "error")
        return
      }

      // Show loading state
      continueBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Connecting...'
      continueBtn.disabled = true

      // Simulate connection delay
      setTimeout(() => {
        // Submit the form
        form.submit()
      }, 1500)
    })
  }

  function showNotification(message, type = "info") {
    // Create notification element
    const notification = document.createElement("div")
    notification.className = `notification ${type}`
    notification.innerHTML = `
            <div class="notification-content">
                <i class="fas ${type === "error" ? "fa-exclamation-circle" : "fa-info-circle"}"></i>
                <span>${message}</span>
            </div>
            <button class="notification-close">
                <i class="fas fa-times"></i>
            </button>
        `

    // Add styles
    notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${type === "error" ? "#fee2e2" : "#dbeafe"};
            color: ${type === "error" ? "#b91c1c" : "#1e40af"};
            padding: 12px 16px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            z-index: 1000;
            display: flex;
            align-items: center;
            gap: 12px;
            max-width: 300px;
            animation: slideInRight 0.3s ease-out;
        `

    // Add to page
    document.body.appendChild(notification)

    // Auto remove after 3 seconds
    setTimeout(() => {
      notification.style.animation = "slideOutRight 0.3s ease-out"
      setTimeout(() => {
        if (notification.parentNode) {
          notification.parentNode.removeChild(notification)
        }
      }, 300)
    }, 3000)

    // Manual close
    notification.querySelector(".notification-close").addEventListener("click", () => {
      notification.style.animation = "slideOutRight 0.3s ease-out"
      setTimeout(() => {
        if (notification.parentNode) {
          notification.parentNode.removeChild(notification)
        }
      }, 300)
    })
  }

  // Add keyboard navigation
  document.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && selectedTenant) {
      form.dispatchEvent(new Event("submit"))
    } else if (e.key === "Escape" && selectedTenant) {
      clearSelection()
    }
  })

  // Add CSS for notifications
  const style = document.createElement("style")
  style.textContent = `
        @keyframes slideInRight {
            from {
                opacity: 0;
                transform: translateX(100%);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }
        
        @keyframes slideOutRight {
            from {
                opacity: 1;
                transform: translateX(0);
            }
            to {
                opacity: 0;
                transform: translateX(100%);
            }
        }
        
        .notification-content {
            display: flex;
            align-items: center;
            gap: 8px;
            flex: 1;
        }
        
        .notification-close {
            background: none;
            border: none;
            cursor: pointer;
            opacity: 0.7;
            transition: opacity 0.2s;
        }
        
        .notification-close:hover {
            opacity: 1;
        }
    `
  document.head.appendChild(style)
})
