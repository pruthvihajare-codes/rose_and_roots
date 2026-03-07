// static/js/account/profile.js

document.addEventListener('DOMContentLoaded', function() {
    
    // ===== TAB NAVIGATION =====
    // The tabs are handled by URL parameters, but we can add smooth scrolling
    const urlParams = new URLSearchParams(window.location.search);
    const activeTab = urlParams.get('tab') || 'profile';

    // ===== AUTO-SCROLL TO PROFILE CONTENT =====
    // Only scroll if we're coming from another page (not a tab switch within the page)
    // or if there's a hash in the URL
    if (document.referrer !== window.location.href && !window.location.hash) {
        setTimeout(function() {
            scrollToProfileContent();
        }, 100);
    }
    
    // Highlight active tab in sidebar
    document.querySelectorAll('.nav-pills .nav-link').forEach(link => {
        if (link.getAttribute('onclick')?.includes(`tab=${activeTab}`)) {
            link.classList.add('active');
        }
    });
    
    // ===== FORM VALIDATION =====
    
    // Phone number validation
    const phoneInputs = document.querySelectorAll('input[type="tel"]');
    phoneInputs.forEach(input => {
        input.addEventListener('input', function(e) {
            this.value = this.value.replace(/[^0-9]/g, '').slice(0, 10);
        });
        
        input.addEventListener('blur', function() {
            validatePhone(this);
        });
    });
    
    // Pincode validation
    const pincodeInput = document.getElementById('pincode');
    if (pincodeInput) {
        pincodeInput.addEventListener('input', function(e) {
            this.value = this.value.replace(/[^0-9]/g, '').slice(0, 6);
        });
        
        pincodeInput.addEventListener('blur', function() {
            validatePincode(this);
        });
    }
    
    // Profile form validation
    const profileForm = document.querySelector('.profile-form');
    if (profileForm) {
        profileForm.addEventListener('submit', function(e) {
            if (!validateProfileForm()) {
                e.preventDefault();
            }
        });
    }
    
    // Address form validation
    const addressForm = document.querySelector('.address-form');
    if (addressForm) {
        addressForm.addEventListener('submit', function(e) {
            if (!validateAddressForm()) {
                e.preventDefault();
            }
        });
    }
    
    // Password form validation
    const passwordForm = document.querySelector('.password-form');
    if (passwordForm) {
        passwordForm.addEventListener('submit', function(e) {
            if (!validatePasswordForm()) {
                e.preventDefault();
            }
        });
    }
    
    // ===== AUTO-SAVE FEATURE (Optional) =====
    // Save form data to localStorage on input (optional enhancement)
    const profileInputs = document.querySelectorAll('.profile-form input, .profile-form select, .profile-form textarea');
    profileInputs.forEach(input => {
        input.addEventListener('input', function() {
            // Optional: Implement auto-save indicator
            console.log('Form changed');
        });
    });
});

// ===== VALIDATION FUNCTIONS =====

function validatePhone(input) {
    const phone = input.value.trim();
    const errorElement = input.nextElementSibling?.classList.contains('invalid-feedback') 
        ? input.nextElementSibling 
        : createErrorElement(input);
    
    if (phone && !/^\d{10}$/.test(phone)) {
        showFieldError(input, errorElement, 'Please enter a valid 10-digit phone number');
        return false;
    } else {
        clearFieldError(input, errorElement);
        return true;
    }
}

function validatePincode(input) {
    const pincode = input.value.trim();
    const errorElement = input.nextElementSibling?.classList.contains('invalid-feedback') 
        ? input.nextElementSibling 
        : createErrorElement(input);
    
    if (pincode && !/^\d{6}$/.test(pincode)) {
        showFieldError(input, errorElement, 'Please enter a valid 6-digit pincode');
        return false;
    } else {
        clearFieldError(input, errorElement);
        return true;
    }
}

function validateProfileForm() {
    let isValid = true;
    let errorMessage = '';
    
    const firstName = document.getElementById('first_name');
    const lastName = document.getElementById('last_name');
    const phone = document.getElementById('phone');
    
    if (!firstName.value.trim()) {
        errorMessage = 'First name is required';
        isValid = false;
    } else if (!lastName.value.trim()) {
        errorMessage = 'Last name is required';
        isValid = false;
    } else if (phone.value.trim() && !/^\d{10}$/.test(phone.value.trim())) {
        errorMessage = 'Please enter a valid 10-digit phone number';
        isValid = false;
    }
    
    if (!isValid) {
        Swal.fire({
            icon: 'error',
            title: 'Validation Error',
            text: errorMessage,
            confirmButtonColor: '#8c0d4f'
        });
    }
    
    return isValid;
}

function validateAddressForm() {
    let isValid = true;
    let errorMessage = '';
    
    const addressLine1 = document.getElementById('address_line1');
    const city = document.getElementById('city');
    const state = document.getElementById('state');
    const pincode = document.getElementById('pincode');
    
    if (!addressLine1.value.trim()) {
        errorMessage = 'Address is required';
        isValid = false;
    } else if (!city.value.trim()) {
        errorMessage = 'City is required';
        isValid = false;
    } else if (!state.value.trim()) {
        errorMessage = 'State is required';
        isValid = false;
    } else if (!pincode.value.trim()) {
        errorMessage = 'Pincode is required';
        isValid = false;
    } else if (!/^\d{6}$/.test(pincode.value.trim())) {
        errorMessage = 'Please enter a valid 6-digit pincode';
        isValid = false;
    }
    
    if (!isValid) {
        Swal.fire({
            icon: 'error',
            title: 'Validation Error',
            text: errorMessage,
            confirmButtonColor: '#8c0d4f'
        });
    }
    
    return isValid;
}

function validatePasswordForm() {
    let isValid = true;
    let errorMessage = '';
    
    const currentPassword = document.getElementById('current_password');
    const newPassword = document.getElementById('new_password');
    const confirmPassword = document.getElementById('confirm_password');
    
    if (!currentPassword.value) {
        errorMessage = 'Current password is required';
        isValid = false;
    } else if (!newPassword.value) {
        errorMessage = 'New password is required';
        isValid = false;
    } else if (newPassword.value.length < 8) {
        errorMessage = 'Password must be at least 8 characters long';
        isValid = false;
    } else if (!/[A-Z]/.test(newPassword.value)) {
        errorMessage = 'Password must contain at least one uppercase letter';
        isValid = false;
    } else if (!/[a-z]/.test(newPassword.value)) {
        errorMessage = 'Password must contain at least one lowercase letter';
        isValid = false;
    } else if (!/[0-9]/.test(newPassword.value)) {
        errorMessage = 'Password must contain at least one number';
        isValid = false;
    } else if (!/[!@#$%^&*(),.?":{}|<>]/.test(newPassword.value)) {
        errorMessage = 'Password must contain at least one special character';
        isValid = false;
    } else if (newPassword.value !== confirmPassword.value) {
        errorMessage = 'New passwords do not match';
        isValid = false;
    }
    
    if (!isValid) {
        Swal.fire({
            icon: 'error',
            title: 'Validation Error',
            text: errorMessage,
            confirmButtonColor: '#8c0d4f'
        });
    }
    
    return isValid;
}

// ===== HELPER FUNCTIONS =====

function createErrorElement(input) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'invalid-feedback';
    input.parentNode.appendChild(errorDiv);
    return errorDiv;
}

function showFieldError(input, errorElement, message) {
    input.classList.add('is-invalid');
    errorElement.textContent = message;
    errorElement.style.display = 'block';
}

function clearFieldError(input, errorElement) {
    input.classList.remove('is-invalid');
    if (errorElement) {
        errorElement.textContent = '';
        errorElement.style.display = 'none';
    }
}

// ===== CONFIRMATION DIALOGS =====

// Optional: Add confirmation for destructive actions
function confirmAddressUpdate() {
    return Swal.fire({
        title: 'Update Address?',
        text: 'Are you sure you want to update your address?',
        icon: 'question',
        showCancelButton: true,
        confirmButtonColor: '#8c0d4f',
        cancelButtonColor: '#6c757d',
        confirmButtonText: 'Yes, update'
    });
}

function confirmPasswordChange() {
    return Swal.fire({
        title: 'Change Password?',
        text: 'You will be logged out after changing your password.',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#8c0d4f',
        cancelButtonColor: '#6c757d',
        confirmButtonText: 'Yes, change'
    });
}

// ===== TAB SWITCHING WITH ANIMATION =====

function switchTab(tabName) {
    const currentTab = document.querySelector('.profile-tab.active');
    const newTab = document.getElementById(`tab-${tabName}`);
    
    if (currentTab && newTab) {
        // Fade out current tab
        currentTab.style.animation = 'fadeOut 0.3s ease';
        setTimeout(() => {
            currentTab.classList.remove('active');
            currentTab.style.animation = '';
            
            // Fade in new tab
            newTab.classList.add('active');
            newTab.style.animation = 'fadeIn 0.4s ease';
            
            // Update URL without page reload
            const url = new URL(window.location);
            url.searchParams.set('tab', tabName);
            window.history.pushState({}, '', url);
            
            // Update active state in sidebar
            document.querySelectorAll('.nav-pills .nav-link').forEach(link => {
                if (link.getAttribute('onclick')?.includes(`tab=${tabName}`)) {
                    link.classList.add('active');
                } else {
                    link.classList.remove('active');
                }
            });
        }, 300);
    }
}

// Add fadeOut animation
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeOut {
        from { opacity: 1; transform: translateY(0); }
        to { opacity: 0; transform: translateY(-10px); }
    }
`;
document.head.appendChild(style);

// ===== SCROLL FUNCTION =====
function scrollToProfileContent() {
    const tabContentContainer = document.querySelector('.tab-content-container');
    if (tabContentContainer) {
        // Get the header height to offset the scroll
        const headerHeight = document.querySelector('.sticky-product-header')?.offsetHeight || 0;
        const navHeight = document.querySelector('.nav-menu-section')?.offsetHeight || 0;
        const topBarHeight = document.querySelector('.top-bar')?.offsetHeight || 0;
        const totalOffset = headerHeight + navHeight + topBarHeight + 20; // 20px extra padding
        
        const elementPosition = tabContentContainer.getBoundingClientRect().top + window.pageYOffset;
        const offsetPosition = elementPosition - totalOffset;
        
        window.scrollTo({
            top: offsetPosition,
            behavior: 'smooth'
        });
    }
}
