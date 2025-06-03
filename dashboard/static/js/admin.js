document.addEventListener('DOMContentLoaded', function() {
  // Toggle sidebar
  const menuToggle = document.getElementById('menuToggle');
  const appContainer = document.querySelector('.app-container');
  
  menuToggle.addEventListener('click', function() {
    if (window.innerWidth <= 576) {
      // For mobile: toggle between expanded and not visible
      if (appContainer.classList.contains('sidebar-expanded')) {
        appContainer.classList.remove('sidebar-expanded');
      } else {
        appContainer.classList.add('sidebar-expanded');
      }
    } else {
      // For desktop: toggle between collapsed and expanded
      appContainer.classList.toggle('sidebar-collapsed');
    }
  });
  
  // Close alert
  const alertClose = document.querySelector('.alert-close');
  if (alertClose) {
    alertClose.addEventListener('click', function() {
      const alert = this.closest('.alert');
      alert.style.opacity = '0';
      setTimeout(() => {
        alert.style.display = 'none';
      }, 300);
    });
  }
  
  // Table row hover effect
  const tableRows = document.querySelectorAll('.data-table tbody tr');
  tableRows.forEach(row => {
    row.addEventListener('mouseenter', function() {
      this.classList.add('hover');
    });
    
    row.addEventListener('mouseleave', function() {
      this.classList.remove('hover');
    });
  });

  // Handle responsive behavior on window resize
  window.addEventListener('resize', function() {
    if (window.innerWidth > 576 && appContainer.classList.contains('sidebar-expanded')) {
      appContainer.classList.remove('sidebar-expanded');
    }
  });
});