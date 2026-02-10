// Authentication JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Initialize password toggles
    initPasswordToggles();
    
    // Initialize form validation
    initFormValidation();
    
    // Initialize form submission
    initFormSubmission();
});

// Password Toggle Functionality
function initPasswordToggles() {
    const toggles = document.querySelectorAll('.password-toggle');
    
    toggles.forEach(toggle => {
        toggle.addEventListener('click', function() {
            const targetId = this.id.replace('toggle', '').replace('Confirm', '');
            const passwordField = document.getElementById(targetId);
            
            if (passwordField) {
                const type = passwordField.getAttribute('type') === 'password' ? 'text' : 'password';
                passwordField.setAttribute('type', type);
                
                // Toggle eye icon
                const icon = this.querySelector('i');
                if (type === 'text') {
                    icon.classList.remove('bi-eye');
                    icon.classList.add('bi-eye-slash');
                } else {
                    icon.classList.remove('bi-eye-slash');
                    icon.classList.add('bi-eye');
                }
            }
        });
    });
}

// Form Validation
function initFormValidation() {
    // Login Form Validation
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            if (!validateLoginForm()) {
                e.preventDefault();
            }
        });
    }
    
    // Register Form Validation
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        // Real-time password validation
        const passwordField = document.getElementById('registerPassword');
        const confirmPasswordField = document.getElementById('confirmPassword');
        
        if (passwordField) {
            passwordField.addEventListener('input', validatePassword);
        }
        
        if (confirmPasswordField) {
            confirmPasswordField.addEventListener('input', validateConfirmPassword);
        }
        
        registerForm.addEventListener('submit', function(e) {
            if (!validateRegisterForm()) {
                e.preventDefault();
            }
        });
    }
}

// Login Form Validation
function validateLoginForm() {
    let isValid = true;
    const emailField = document.getElementById('loginEmail');
    const passwordField = document.getElementById('loginPassword');
    
    // Clear previous errors
    clearErrors();
    
    // Validate email
    if (!emailField.value.trim()) {
        showError(emailField, 'emailError', 'Email is required.');
        isValid = false;
    } else if (!isValidEmail(emailField.value)) {
        showError(emailField, 'emailError', 'Please enter a valid email address.');
        isValid = false;
    }
    
    // Validate password
    if (!passwordField.value) {
        showError(passwordField, 'passwordError', 'Password is required.');
        isValid = false;
    }
    
    return isValid;
}

// Register Form Validation
function validateRegisterForm() {
    let isValid = true;
    const form = document.getElementById('registerForm');
    
    if (!form) return false;
    
    // Clear previous errors
    clearErrors();
    
    // Validate first name
    const firstName = document.getElementById('firstName');
    if (!firstName.value.trim()) {
        showError(firstName, 'firstNameError', 'First name is required.');
        isValid = false;
    }
    
    // Validate last name
    const lastName = document.getElementById('lastName');
    if (!lastName.value.trim()) {
        showError(lastName, 'lastNameError', 'Last name is required.');
        isValid = false;
    }
    
    // Validate email
    const email = document.getElementById('registerEmail');
    if (!email.value.trim()) {
        showError(email, 'emailError', 'Email is required.');
        isValid = false;
    } else if (!isValidEmail(email.value)) {
        showError(email, 'emailError', 'Please enter a valid email address.');
        isValid = false;
    }
    
    // Validate password
    const password = document.getElementById('registerPassword');
    const passwordValidation = validatePasswordStrength(password.value);
    if (!password.value) {
        showError(password, 'passwordError', 'Password is required.');
        isValid = false;
    } else if (!passwordValidation.isValid) {
        showError(password, 'passwordError', passwordValidation.message);
        isValid = false;
    }
    
    // Validate confirm password
    const confirmPassword = document.getElementById('confirmPassword');
    if (!confirmPassword.value) {
        showError(confirmPassword, 'confirmPasswordError', 'Please confirm your password.');
        isValid = false;
    } else if (password.value !== confirmPassword.value) {
        showError(confirmPassword, 'confirmPasswordError', 'Passwords do not match.');
        isValid = false;
    }
    
    // Validate terms
    const terms = document.getElementById('terms');
    if (!terms.checked) {
        showError(terms, 'termsError', 'You must agree to the terms and conditions.');
        isValid = false;
    }
    
    return isValid;
}

// Real-time Password Validation
function validatePassword() {
    const password = this ? this.value : document.getElementById('registerPassword').value;
    const validation = validatePasswordStrength(password);
    
    // Update requirement indicators
    updateRequirementIndicators(password);
    
    // Update password match indicator
    validateConfirmPassword();
    
    // Show/hide error message
    const passwordField = document.getElementById('registerPassword');
    const errorElement = document.getElementById('passwordError');
    
    if (!validation.isValid && password.length > 0) {
        showError(passwordField, 'passwordError', validation.message);
    } else {
        clearError(passwordField, 'passwordError');
    }
}

// Real-time Confirm Password Validation
function validateConfirmPassword() {
    const password = document.getElementById('registerPassword').value;
    const confirmPassword = this ? this.value : document.getElementById('confirmPassword').value;
    const matchIndicator = document.getElementById('passwordMatch');
    
    if (password && confirmPassword) {
        if (password === confirmPassword) {
            matchIndicator.classList.remove('d-none');
            matchIndicator.querySelector('i').className = 'bi bi-check-circle text-success';
            matchIndicator.querySelector('span').textContent = 'Passwords match';
            
            const confirmPasswordField = document.getElementById('confirmPassword');
            clearError(confirmPasswordField, 'confirmPasswordError');
        } else {
            matchIndicator.classList.remove('d-none');
            matchIndicator.querySelector('i').className = 'bi bi-x-circle text-danger';
            matchIndicator.querySelector('span').textContent = 'Passwords do not match';
        }
    } else {
        matchIndicator.classList.add('d-none');
    }
}

// Update Password Requirement Indicators
function updateRequirementIndicators(password) {
    const requirements = {
        'length': password.length >= 8,
        'uppercase': /[A-Z]/.test(password),
        'lowercase': /[a-z]/.test(password),
        'number': /\d/.test(password),
        'special': /[!@#$%^&*(),.?":{}|<>]/.test(password)
    };
    
    for (const [key, met] of Object.entries(requirements)) {
        const item = document.querySelector(`.req-item[data-check="${key}"]`);
        if (item) {
            const icon = item.querySelector('i');
            if (met) {
                item.classList.add('requirement-met');
                icon.classList.remove('bi-circle');
                icon.classList.add('bi-check-circle', 'text-success');
            } else {
                item.classList.remove('requirement-met');
                icon.classList.remove('bi-check-circle', 'text-success');
                icon.classList.add('bi-circle');
            }
        }
    }
}

// Validate Password Strength
function validatePasswordStrength(password) {
    if (password.length < 8) {
        return { isValid: false, message: 'Password must be at least 8 characters long.' };
    }
    
    if (!/[A-Z]/.test(password)) {
        return { isValid: false, message: 'Password must contain at least one uppercase letter.' };
    }
    
    if (!/[a-z]/.test(password)) {
        return { isValid: false, message: 'Password must contain at least one lowercase letter.' };
    }
    
    if (!/\d/.test(password)) {
        return { isValid: false, message: 'Password must contain at least one number.' };
    }
    
    if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
        return { isValid: false, message: 'Password must contain at least one special character.' };
    }
    
    return { isValid: true, message: '' };
}

// Email Validation
function isValidEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

// Show Error
function showError(field, errorId, message) {
    field.classList.add('is-invalid');
    const errorElement = document.getElementById(errorId);
    if (errorElement) {
        errorElement.textContent = message;
        errorElement.style.display = 'block';
    }
}

// Clear Error
function clearError(field, errorId) {
    field.classList.remove('is-invalid');
    const errorElement = document.getElementById(errorId);
    if (errorElement) {
        errorElement.style.display = 'none';
    }
}

// Clear All Errors
function clearErrors() {
    const invalidFields = document.querySelectorAll('.is-invalid');
    invalidFields.forEach(field => {
        field.classList.remove('is-invalid');
    });
    
    const errorElements = document.querySelectorAll('.invalid-feedback');
    errorElements.forEach(element => {
        element.style.display = 'none';
    });
}

// Form Submission
function initFormSubmission() {
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    
    if (loginForm) {
        loginForm.addEventListener('submit', handleLoginSubmit);
    }
    
    if (registerForm) {
        registerForm.addEventListener('submit', handleRegisterSubmit);
    }
}

// Handle Login Submission
async function handleLoginSubmit(e) {
    e.preventDefault();
    
    if (!validateLoginForm()) return;
    
    const form = e.target;
    const submitBtn = form.querySelector('.auth-submit-btn');
    const btnText = submitBtn.querySelector('.btn-text');
    const btnSpinner = submitBtn.querySelector('.btn-spinner');
    
    // Show loading state
    submitBtn.disabled = true;
    btnText.classList.add('d-none');
    btnSpinner.classList.remove('d-none');
    
    // Prepare form data
    const formData = {
        email: document.getElementById('loginEmail').value.trim(),
        password: document.getElementById('loginPassword').value,
        remember_me: document.getElementById('rememberMe').checked,
        csrfmiddlewaretoken: form.querySelector('[name=csrfmiddlewaretoken]').value
    };
    
    try {
        const response = await fetch('/accounts/api/login/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': formData.csrfmiddlewaretoken
            },
            body: JSON.stringify(formData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage('success', data.message);
            setTimeout(() => {
                window.location.href = data.redirect_url || '/';
            }, 1500);
        } else {
            showMessage('danger', data.message);
            submitBtn.disabled = false;
            btnText.classList.remove('d-none');
            btnSpinner.classList.add('d-none');
        }
        
    } catch (error) {
        showMessage('danger', 'An error occurred. Please try again.');
        submitBtn.disabled = false;
        btnText.classList.remove('d-none');
        btnSpinner.classList.add('d-none');
        console.error('Login error:', error);
    }
}

// Handle Register Submission
async function handleRegisterSubmit(e) {
    e.preventDefault();
    
    if (!validateRegisterForm()) return;
    
    const form = e.target;
    const submitBtn = form.querySelector('.auth-submit-btn');
    const btnText = submitBtn.querySelector('.btn-text');
    const btnSpinner = submitBtn.querySelector('.btn-spinner');
    
    // Show loading state
    submitBtn.disabled = true;
    btnText.classList.add('d-none');
    btnSpinner.classList.remove('d-none');
    
    // Prepare form data
    const formData = {
        first_name: document.getElementById('firstName').value.trim(),
        last_name: document.getElementById('lastName').value.trim(),
        email: document.getElementById('registerEmail').value.trim(),
        password: document.getElementById('registerPassword').value,
        confirm_password: document.getElementById('confirmPassword').value,
        terms: document.getElementById('terms').checked,
        csrfmiddlewaretoken: form.querySelector('[name=csrfmiddlewaretoken]').value
    };
    
    try {
        const response = await fetch('/accounts/api/register/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': formData.csrfmiddlewaretoken
            },
            body: JSON.stringify(formData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage('success', data.message);
            setTimeout(() => {
                window.location.href = data.redirect_url || '/';
            }, 1500);
        } else {
            // Display field-specific errors
            if (data.errors) {
                for (const [field, message] of Object.entries(data.errors)) {
                    const fieldElement = document.getElementById(field === 'confirm_password' ? 'confirmPassword' : field);
                    const errorId = field === 'confirm_password' ? 'confirmPasswordError' : `${field}Error`;
                    if (fieldElement) {
                        showError(fieldElement, errorId, message);
                    }
                }
                showMessage('danger', data.message || 'Please correct the errors below.');
            } else {
                showMessage('danger', data.message || 'Registration failed. Please try again.');
            }
            
            submitBtn.disabled = false;
            btnText.classList.remove('d-none');
            btnSpinner.classList.add('d-none');
        }
        
    } catch (error) {
        showMessage('danger', 'An error occurred. Please try again.');
        submitBtn.disabled = false;
        btnText.classList.remove('d-none');
        btnSpinner.classList.add('d-none');
        console.error('Registration error:', error);
    }
}

// Show Message
function showMessage(type, message) {
    const messagesContainer = document.getElementById('authMessages');
    const messageText = document.getElementById('messageText');
    const alert = messagesContainer.querySelector('.alert');
    
    if (messagesContainer && messageText && alert) {
        // Set message and type
        messageText.textContent = message;
        alert.className = `alert alert-${type} alert-dismissible fade show`;
        
        // Show container
        messagesContainer.classList.remove('d-none');
        
        // Auto-hide after 5 seconds for success messages
        if (type === 'success') {
            setTimeout(() => {
                hideMessage();
            }, 5000);
        }
    }
}

// Hide Message
function hideMessage() {
    const messagesContainer = document.getElementById('authMessages');
    if (messagesContainer) {
        messagesContainer.classList.add('d-none');
    }
}