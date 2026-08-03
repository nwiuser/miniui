// APEX-OSS JavaScript
// This provides basic client-side functionality for the APEX-OSS application

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    initTooltips();

    // Initialize form validations
    initFormValidations();

    // Initialize table sorting if needed
    initTableSorting();

    // Handle flash messages
    handleFlashMessages();
});

/**
 * Initialize tooltips for elements with title attributes
 */
function initTooltips() {
    const elements = document.querySelectorAll('[title]');
    elements.forEach(el => {
        // Basic tooltip implementation - in a real app, you might use a library
        el.addEventListener('mouseenter', function(e) {
            const tooltip = document.createElement('div');
            tooltip.className = 'tooltip';
            tooltip.innerHTML = this.title;
            tooltip.style.position = 'absolute';
            tooltip.style.backgroundColor = '#333';
            tooltip.style.color = '#fff';
            tooltip.style.padding = '5px 10px';
            tooltip.style.borderRadius = '3px';
            tooltip.style.fontSize = '12px';
            tooltip.style.zIndex = '1000';
            tooltip.style.whiteSpace = 'nowrap';

            document.body.appendChild(tooltip);

            const rect = this.getBoundingClientRect();
            tooltip.style.top = (rect.bottom + window.scrollY + 5) + 'px';
            tooltip.style.left = (rect.left + window.scrollX) + 'px';

            this._tooltip = tooltip;
        });

        el.addEventListener('mouseleave', function() {
            if (this._tooltip) {
                this._tooltip.remove();
                this._tooltip = null;
            }
        });
    });
}

/**
 * Initialize form validations and enhancements
 */
function initFormValidations() {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        // Add CSS classes to required fields
        const requiredInputs = form.querySelectorAll('[required]');
        requiredInputs.forEach(input => {
            input.classList.add('required-field');
        });

        // Real-time validation for certain fields
        form.addEventListener('input', function(e) {
            const target = e.target;
            if (target.hasAttribute('data-validate')) {
                validateField(target);
            }
        });

        // Form submission handling
        form.addEventListener('submit', function(e) {
            // HTML5 validation will handle required fields and basic validation
            // Custom validation can be added here if needed
        });
    });
}

/**
 * Validate a single field based on its data-validation attribute
 * @param {HTMLElement} field - The form field to validate
 */
function validateField(field) {
    const validationType = field.getAttribute('data-validate');
    const value = field.value;
    const isValid = {};

    switch (validationType) {
        case 'email':
            isValid.valid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
            break;
        case 'number':
            isValid.valid = !isNaN(parseFloat(value)) && isFinite(value);
            break;
        case 'min-length':
            const minLength = parseInt(field.getAttribute('data-min-length') || '0');
            isValid.valid = value.length >= minLength;
            break;
        case 'max-length':
            const maxLength = parseInt(field.getAttribute('data-max-length') || '1000000');
            isValid.valid = value.length <= maxLength;
            break;
        case 'pattern':
            const pattern = new RegExp(field.getAttribute('data-pattern'));
            isValid.valid = pattern.test(value);
            break;
        default:
            isValid.valid = true; // No validation specified
    }

    // Update UI based on validation result
    if (isValid.valid) {
        field.classList.remove('invalid');
        field.classList.add('valid');
        const errorEl = field.parentNode.querySelector('.field-error');
        if (errorEl) {
            errorEl.remove();
        }
    } else {
        field.classList.remove('valid');
        field.classList.add('invalid');
        let errorEl = field.parentNode.querySelector('.field-error');
        if (!errorEl) {
            errorEl = document.createElement('div');
            errorEl.className = 'field-error';
            errorEl.style.color = '#e74c3c';
            errorEl.style.fontSize = '0.9em';
            errorEl.style.marginTop = '5px';
            field.parentNode.appendChild(errorEl);
        }
        errorEl.textContent = field.getAttribute('data-error-message') || 'Invalid value';
    }
}

/**
 * Initialize table sorting capabilities
 */
function initTableSorting() {
    const tables = document.querySelectorAll('.sortable-table');
    tables.forEach(table => {
        const headers = table.querySelectorAll('th');
        headers.forEach((header, index) => {
            if (header.getAttribute('data-sortable') !== 'false') {
                header.style.cursor = 'pointer';
                header.title = 'Click to sort';

                header.addEventListener('click', function() {
                    sortTable(table, index, this.getAttribute('data-sort-direction') === 'desc');
                    // Toggle sort direction for next click
                    this.setAttribute('data-sort-direction',
                        this.getAttribute('data-sort-direction') === 'desc' ? 'asc' : 'desc');
                });

                // Set initial sort direction
                if (!header.hasAttribute('data-sort-direction')) {
                    header.setAttribute('data-sort-direction', 'asc');
                }
            }
        });
    });
}

/**
 * Sort a table by a column index
 * @param {HTMLTableElement} table - The table to sort
 * @param {number} columnIndex - The index of the column to sort by
 * @param {boolean} isDescending - Whether to sort in descending order
 */
function sortTable(table, columnIndex, isDescending = false) {
    const tbody = table.querySelector('tbody');
    if (!tbody) return;

    const rows = Array.from(tbody.querySelectorAll('tr'));

    // Sort rows based on cell content
    rows.sort((rowA, rowB) => {
        const cellA = rowA.cells[columnIndex].textContent.trim();
        const cellB = rowB.cells[columnIndex].textContent.trim();

        // Try to parse as numbers for numeric sorting
        const numA = parseFloat(cellA);
        const numB = parseFloat(cellB);

        if (!isNaN(numA) && !isNaN(numB)) {
            return isDescending ? numB - numA : numA - numB;
        }

        // String comparison
        return isDescending
            ? cellB.localeCompare(cellA)
            : cellA.localeCompare(cellB);
    });

    // Remove existing rows and append sorted ones
    while (tbody.firstChild) {
        tbody.removeChild(tbody.firstChild);
    }

    rows.forEach(row => tbody.appendChild(row));
}

/**
 * Handle flash messages (temporary notifications)
 */
function flashMessage(message, type = 'info') {
    // Remove any existing flash messages
    const existing = document.querySelector('.flash-message');
    if (existing) {
        existing.remove();
    }

    // Create flash message element
    const flash = document.createElement('div');
    flash.className = `flash-message flash-${type}`;
    flash.innerHTML = `
        <span class="flash-message-content">${message}</span>
        <button class="flash-message-close">&times;</button>
    `;

    // Style the flash message
    flash.style.position = 'fixed';
    flash.style.top = '20px';
    flash.style.right = '20px';
    flash.style.padding = '15px';
    flash.style.borderRadius = '4px';
    flash.style.boxShadow = '0 2px 10px rgba(0,0,0,0.1)';
    flash.style.zIndex = '1000';
    flash.style.minWidth = '250px';

    // Set background color based on type
    switch (type) {
        case 'success':
            flash.style.backgroundColor = '#d4edda';
            flash.style.borderColor = '#c3e6cb';
            flash.style.color = '#155724';
            break;
        case 'error':
            flash.style.backgroundColor = '#f8d7da';
            flash.style.borderColor = '#f5c6cb';
            flash.style.color = '#721c24';
            break;
        case 'warning':
            flash.style.backgroundColor = '#fff3cd';
            flash.style.borderColor = '#ffeaa7';
            flash.style.color = '#856404';
            break;
        case 'info':
        default:
            flash.style.backgroundColor = '#d1ecf1';
            flash.style.borderColor = '#bee5eb';
            flight.style.color = '#0c5460';
            break;
    }

    // Add close button functionality
    const closeBtn = flash.querySelector('.flash-message-close');
    closeBtn.style.background = 'transparent';
    closeBtn.style.border = 'none';
    closeBtn.style.fontSize = '1.5em';
    closeBtn.style.lineHeight = '1';
    closeBtn.style.cursor = 'pointer';
    closeBtn.style.position = 'absolute';
    closeBtn.style.top = '5px';
    closeBtn.style.right = '10px';

    closeBtn.addEventListener('click', function() {
        flash.remove();
    });

    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (flash.parentNode) {
            flash.remove();
        }
    }, 5000);

    // Add to document
    document.body.appendChild(flash);
}

/**
 * Handle any existing flash messages in the DOM
 */
function handleFlashMessages() {
    // This would handle flash messages that are already in the HTML
    // For example, if they were rendered server-side
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(msg => {
        // Add click-to-dismiss functionality
        msg.addEventListener('click', function() {
            this.style.opacity = '0';
            setTimeout(() => {
                if (this.parentNode) {
                    this.parentNode.removeChild(this);
                }
            }, 300);
        });
    });
}

// Make functions available globally if needed
window.flashMessage = window.flashMessage || flashMessage;

// Export for potential module usage (if using a module system)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        initTooltips,
        initFormValidations,
        initTableSorting,
        sortTable,
        flashMessage,
        handleFlashMessages
    };
}