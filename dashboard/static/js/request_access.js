document.addEventListener("DOMContentLoaded", () => {
  let currentStep = 1
  const totalSteps = 3

  // Elements
  const form = document.getElementById("requestForm")
  const prevBtn = document.getElementById("prevBtn")
  const nextBtn = document.getElementById("nextBtn")
  const submitBtn = document.getElementById("submitBtn")
  const uploadArea = document.getElementById("uploadArea")
  const fileInput = document.getElementById("proof")
  const fileList = document.getElementById("fileList")
  const reasonTextarea = document.getElementById("reason")
  const charCount = document.getElementById("charCount")

  // Initialize
  updateStepDisplay()
  setupFileUpload()
  setupFormValidation()
  setupCharacterCounter()

  // Step navigation
  nextBtn.addEventListener("click", () => {
    if (validateCurrentStep()) {
      if (currentStep < totalSteps) {
        currentStep++
        updateStepDisplay()
      }
    }
  })

  prevBtn.addEventListener("click", () => {
    if (currentStep > 1) {
      currentStep--
      updateStepDisplay()
    }
  })

  // Form submission
  form.addEventListener("submit", (e) => {
    e.preventDefault()
    if (validateAllSteps()) {
      // Show loading state
      submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Submitting...'
      submitBtn.disabled = true

      // Simulate form submission (replace with actual submission)
      setTimeout(() => {
        alert("Request submitted successfully!")
        submitBtn.innerHTML = '<i class="fas fa-paper-plane"></i> Submit Request'
        submitBtn.disabled = false
      }, 2000)
    }
  })

  function updateStepDisplay() {
    // Update step indicators
    document.querySelectorAll(".step").forEach((step, index) => {
      const stepNum = index + 1
      step.classList.remove("active", "completed")

      if (stepNum === currentStep) {
        step.classList.add("active")
      } else if (stepNum < currentStep) {
        step.classList.add("completed")
      }
    })

    // Update form steps
    document.querySelectorAll(".form-step").forEach((step, index) => {
      step.classList.remove("active")
      if (index + 1 === currentStep) {
        step.classList.add("active")
      }
    })

    // Update navigation buttons
    prevBtn.style.display = currentStep === 1 ? "none" : "inline-flex"
    nextBtn.style.display = currentStep === totalSteps ? "none" : "inline-flex"
    submitBtn.style.display = currentStep === totalSteps ? "inline-flex" : "none"
  }

  function validateCurrentStep() {
    const currentStepElement = document.querySelector(`.form-step[data-step="${currentStep}"]`)
    const requiredInputs = currentStepElement.querySelectorAll("input[required], textarea[required]")
    let isValid = true

    requiredInputs.forEach((input) => {
      if (!input.value.trim()) {
        showFieldError(input, "This field is required")
        isValid = false
      } else {
        showFieldSuccess(input)
      }
    })

    return isValid
  }

  function validateAllSteps() {
    let isValid = true
    for (let step = 1; step <= totalSteps; step++) {
      const stepElement = document.querySelector(`.form-step[data-step="${step}"]`)
      const requiredInputs = stepElement.querySelectorAll("input[required], textarea[required]")

      requiredInputs.forEach((input) => {
        if (!input.value.trim()) {
          isValid = false
        }
      })
    }
    return isValid
  }

  function showFieldError(input, message) {
    const container = input.closest(".input-container") || input.closest(".textarea-container")
    container.classList.remove("success")
    container.classList.add("error")

    // Remove existing error message
    const existingError = container.parentNode.querySelector(".error-message")
    if (existingError) {
      existingError.remove()
    }

    // Add error message
    const errorDiv = document.createElement("div")
    errorDiv.className = "error-message"
    errorDiv.style.color = "var(--danger)"
    errorDiv.style.fontSize = "12px"
    errorDiv.style.marginTop = "4px"
    errorDiv.textContent = message
    container.parentNode.appendChild(errorDiv)
  }

  function showFieldSuccess(input) {
    const container = input.closest(".input-container") || input.closest(".textarea-container")
    container.classList.remove("error")
    container.classList.add("success")

    // Remove error message
    const existingError = container.parentNode.querySelector(".error-message")
    if (existingError) {
      existingError.remove()
    }
  }

  function setupFileUpload() {
    let selectedFiles = []

    // Drag and drop
    uploadArea.addEventListener("dragover", (e) => {
      e.preventDefault()
      uploadArea.classList.add("drag-over")
    })

    uploadArea.addEventListener("dragleave", (e) => {
      e.preventDefault()
      uploadArea.classList.remove("drag-over")
    })

    uploadArea.addEventListener("drop", (e) => {
      e.preventDefault()
      uploadArea.classList.remove("drag-over")

      const files = Array.from(e.dataTransfer.files)
      handleFiles(files)
    })

    // File input change
    fileInput.addEventListener("change", (e) => {
      const files = Array.from(e.target.files)
      handleFiles(files)
    })

    function handleFiles(files) {
      files.forEach((file) => {
        if (isValidFile(file)) {
          selectedFiles.push(file)
          addFileToList(file)
        }
      })
    }

    function isValidFile(file) {
      const allowedTypes = [
        "application/pdf",
        "image/jpeg",
        "image/jpg",
        "image/png",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      ]
      const maxSize = 10 * 1024 * 1024 // 10MB

      if (!allowedTypes.includes(file.type)) {
        alert("Invalid file type. Please upload PDF, JPG, PNG, or DOC files.")
        return false
      }

      if (file.size > maxSize) {
        alert("File size too large. Please upload files smaller than 10MB.")
        return false
      }

      return true
    }

    function addFileToList(file) {
      const fileItem = document.createElement("div")
      fileItem.className = "file-item"
      fileItem.innerHTML = `
                <div class="file-info">
                    <div class="file-icon">
                        <i class="fas ${getFileIcon(file.type)}"></i>
                    </div>
                    <div class="file-details">
                        <h4>${file.name}</h4>
                        <p>${formatFileSize(file.size)}</p>
                    </div>
                </div>
                <div class="file-actions">
                    <button type="button" class="file-remove" onclick="removeFile('${file.name}')">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            `

      fileList.appendChild(fileItem)
    }

    function getFileIcon(fileType) {
      if (fileType.includes("pdf")) return "fa-file-pdf"
      if (fileType.includes("image")) return "fa-file-image"
      if (fileType.includes("word")) return "fa-file-word"
      return "fa-file"
    }

    function formatFileSize(bytes) {
      if (bytes === 0) return "0 Bytes"
      const k = 1024
      const sizes = ["Bytes", "KB", "MB", "GB"]
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return Number.parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i]
    }

    // Make removeFile function global
    window.removeFile = (fileName) => {
      selectedFiles = selectedFiles.filter((file) => file.name !== fileName)
      const fileItems = fileList.querySelectorAll(".file-item")
      fileItems.forEach((item) => {
        if (item.querySelector(".file-details h4").textContent === fileName) {
          item.remove()
        }
      })
    }
  }

  function setupFormValidation() {
    // Real-time validation for inputs
    const inputs = document.querySelectorAll("input, textarea")
    inputs.forEach((input) => {
      input.addEventListener("blur", function () {
        if (this.hasAttribute("required") && !this.value.trim()) {
          showFieldError(this, "This field is required")
        } else if (this.value.trim()) {
          showFieldSuccess(this)
        }
      })

      input.addEventListener("input", function () {
        const container = this.closest(".input-container") || this.closest(".textarea-container")
        if (container.classList.contains("error") && this.value.trim()) {
          showFieldSuccess(this)
        }
      })
    })

    // Email validation
    const emailInput = document.getElementById("email")
    if (emailInput) {
      emailInput.addEventListener("blur", function () {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
        if (this.value && !emailRegex.test(this.value)) {
          showFieldError(this, "Please enter a valid email address")
        } else if (this.value) {
          showFieldSuccess(this)
        }
      })
    }
  }

  function setupCharacterCounter() {
    if (reasonTextarea && charCount) {
      reasonTextarea.addEventListener("input", function () {
        const count = this.value.length
        charCount.textContent = count

        if (count > 500) {
          charCount.style.color = "var(--danger)"
        } else if (count > 400) {
          charCount.style.color = "var(--warning)"
        } else {
          charCount.style.color = "var(--gray)"
        }
      })
    }
  }
})
