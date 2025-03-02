(function() {
    // Define Bootstrap's default breakpoints in pixels
    const breakpoints = {
      xs: 0,
      sm: 576,
      md: 768,
      lg: 992,
      xl: 1300,
      xxl: 1400
    };

    // Function to evaluate the condition string based on current viewport width
    function evaluateCondition(conditionStr) {
      if (!conditionStr) return true;
      
      conditionStr = conditionStr.trim();
      const currentWidth = window.innerWidth;
      
      // Handle multiple conditions in parentheses, e.g. "(>md<xl)"
      if (conditionStr.startsWith('(') && conditionStr.endsWith(')')) {
        const inner = conditionStr.slice(1, -1);
        const parts = inner.match(/([<>])([a-z]+)/g) || [];
        
        return parts.every(part => {
          const operator = part.charAt(0);
          const bpKey = part.slice(1);
          const bpValue = breakpoints[bpKey];
          
          if (!bpValue) return true; // Skip unknown breakpoints
          return operator === '>' ? currentWidth > bpValue : currentWidth < bpValue;
        });
      } 
      // Handle single condition, e.g. ">xl" or "<lg"
      else {
        const operator = conditionStr.charAt(0);
        const bpKey = conditionStr.slice(1);
        const bpValue = breakpoints[bpKey];
        
        if (!bpValue) return true;
        return operator === '>' ? currentWidth > bpValue : currentWidth < bpValue;
      }
    }

    // Safely get Bootstrap popover instance
    function getPopoverInstance(element) {
      if (!bootstrap || !bootstrap.Popover || !bootstrap.Popover.getInstance) {
        return null;
      }
      
      try {
        return bootstrap.Popover.getInstance(element);
      } catch (err) {
        console.warn("Error getting popover instance:", err);
        return null;
      }
    }
    
    // Function to handle responsive popovers
    function handleResponsivePopovers() {
      // Ensure Bootstrap is available
      if (typeof bootstrap === 'undefined' || !bootstrap.Popover) {
        console.error("Bootstrap Popover is not available");
        return;
      }
      
      // 1. First, destroy any existing popovers to avoid duplication
      document.querySelectorAll('[data-bs-toggle="popover"]').forEach(elem => {
        try {
          const instance = bootstrap.Popover.getInstance(elem);
          if (instance) {
            instance.dispose();
          }
        } catch (err) {
          // Ignore errors
        }
      });
      
      // 2. Process all elements with responsive attribute
      document.querySelectorAll('[data-bs-toggle="popover"][data-bs-responsive]').forEach(elem => {
        const condition = elem.getAttribute('data-bs-responsive');
        const shouldShow = evaluateCondition(condition);
        
        if (shouldShow) {
          try {
            new bootstrap.Popover(elem, {
              container: 'body',
              trigger: elem.getAttribute('data-bs-trigger') || 'hover'
            });
          } catch (err) {
            console.error('Error creating popover:', err);
          }
        }
      });
      
      // 3. For popovers without the responsive attribute, always initialize them
      document.querySelectorAll('[data-bs-toggle="popover"]:not([data-bs-responsive])').forEach(elem => {
        try {
          new bootstrap.Popover(elem, {
            container: 'body',
            trigger: elem.getAttribute('data-bs-trigger') || 'hover'
          });
        } catch (err) {
          console.error('Error creating popover:', err);
        }
      });
    }

    // Initialize on DOMContentLoaded
    document.addEventListener('DOMContentLoaded', function() {
      // Add a small delay to ensure Bootstrap is fully loaded
      setTimeout(handleResponsivePopovers, 100);
    });
    
    // Re-initialize on resize
    window.addEventListener('resize', handleResponsivePopovers);
    
    // Also initialize when window load is complete
    window.addEventListener('load', handleResponsivePopovers);
    
    // Add debugging function to global scope
    window.reinitPopovers = handleResponsivePopovers;
  })();