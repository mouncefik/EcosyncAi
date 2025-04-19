/**
 * Main JavaScript file for Energy Insight application
 */
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Add event listeners for device selection
    const deviceCheckboxes = document.querySelectorAll('input[name="devices"]');
    if (deviceCheckboxes.length > 0) {
        // Select All checkbox functionality
        const selectAllCheckbox = document.getElementById('selectAllDevices');
        if (selectAllCheckbox) {
            selectAllCheckbox.addEventListener('change', function() {
                const isChecked = this.checked;
                deviceCheckboxes.forEach(checkbox => {
                    checkbox.checked = isChecked;
                });
            });
        }

        // Update Select All state based on individual selections
        deviceCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                if (selectAllCheckbox) {
                    selectAllCheckbox.checked = [...deviceCheckboxes].every(cb => cb.checked);
                    selectAllCheckbox.indeterminate = !selectAllCheckbox.checked && 
                        [...deviceCheckboxes].some(cb => cb.checked);
                }
            });
        });
    }

    // Form validation for consumption form
    const consumptionForm = document.getElementById('consumptionForm');
    if (consumptionForm) {
        consumptionForm.addEventListener('submit', function(event) {
            const area = parseFloat(document.getElementById('area').value);
            const rooms = parseInt(document.getElementById('rooms').value);
            const occupants = parseInt(document.getElementById('occupants').value);
            const selectedDevices = document.querySelectorAll('input[name="devices"]:checked');

            let isValid = true;
            let errorMessage = '';

            if (isNaN(area) || area <= 0) {
                errorMessage = 'Please enter a valid area.';
                isValid = false;
            } else if (isNaN(rooms) || rooms <= 0) {
                errorMessage = 'Please enter a valid number of rooms.';
                isValid = false;
            } else if (isNaN(occupants) || occupants <= 0) {
                errorMessage = 'Please enter a valid number of occupants.';
                isValid = false;
            } else if (selectedDevices.length === 0) {
                errorMessage = 'Please select at least one device.';
                isValid = false;
            }

            if (!isValid) {
                event.preventDefault();
                alert(errorMessage);
            }
        });
    }

    // Form validation for generation form
    const generationForm = document.getElementById('generationForm');
    if (generationForm) {
        generationForm.addEventListener('submit', function(event) {
            const city = document.getElementById('city').value.trim();
            
            if (!city) {
                event.preventDefault();
                alert('Please enter a city name.');
            }
        });
    }

    // Animate numbers in stats
    const animateValue = (element, start, end, duration) => {
        if (!element) return;
        
        let startTimestamp = null;
        const step = (timestamp) => {
            if (!startTimestamp) startTimestamp = timestamp;
            const progress = Math.min((timestamp - startTimestamp) / duration, 1);
            const value = Math.floor(progress * (end - start) + start);
            element.textContent = value.toLocaleString();
            if (progress < 1) {
                window.requestAnimationFrame(step);
            } else {
                element.textContent = end.toLocaleString();
            }
        };
        window.requestAnimationFrame(step);
    };

    // Animate stat numbers on page load
    const statElements = document.querySelectorAll('.animate-value');
    statElements.forEach(el => {
        const end = parseInt(el.getAttribute('data-value') || el.textContent, 10);
        animateValue(el, 0, end, 1000);
    });
});
