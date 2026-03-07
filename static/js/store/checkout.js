// static/js/store/checkout.js

document.addEventListener('DOMContentLoaded', function() {
    
    // Initialize form validation only
    initializeFormValidation();
    
    // Initialize pincode lookup (optional)
    initializePincodeLookup();
});

// Remove initializeDeliveryOptions function since delivery is fixed

function initializeFormValidation() {
    const form = document.getElementById('checkoutForm');
    if (!form) return;
    
    // Phone number formatting
    const phoneInput = document.getElementById('phone');
    if (phoneInput) {
        phoneInput.addEventListener('input', function(e) {
            this.value = this.value.replace(/[^0-9]/g, '').slice(0, 10);
        });
    }
    
    // Pincode formatting
    const pincodeInput = document.getElementById('pincode');
    if (pincodeInput) {
        pincodeInput.addEventListener('input', function(e) {
            this.value = this.value.replace(/[^0-9]/g, '').slice(0, 6);
        });
    }
    
    // Real-time validation on blur
    const inputs = form.querySelectorAll('input[required], select[required]');
    inputs.forEach(input => {
        input.addEventListener('blur', function() {
            validateField(this);
        });
    });
}

function validateField(field) {
    if (!field.value.trim()) {
        field.classList.add('is-invalid');
        return false;
    }
    
    // Email validation
    if (field.id === 'email') {
        const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailPattern.test(field.value)) {
            field.classList.add('is-invalid');
            return false;
        }
    }
    
    // Phone validation
    if (field.id === 'phone') {
        if (!/^\d{10}$/.test(field.value)) {
            field.classList.add('is-invalid');
            return false;
        }
    }
    
    // Pincode validation
    if (field.id === 'pincode') {
        if (!/^\d{6}$/.test(field.value)) {
            field.classList.add('is-invalid');
            return false;
        }
    }
    
    field.classList.remove('is-invalid');
    return true;
}

function initializePincodeLookup() {
    const pincodeInput = document.getElementById('pincode');
    if (!pincodeInput) return;
    
    pincodeInput.addEventListener('blur', function() {
        const pincode = this.value.trim();
        if (pincode.length === 6) {
            // Optional: Lookup pincode via API
            console.log('Looking up pincode:', pincode);
        }
    });
}

