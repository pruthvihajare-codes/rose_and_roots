// static/js/masters/user-form.js

document.addEventListener('DOMContentLoaded', function() {
    
    // ===== Password Toggle Functionality =====
    // Make togglePassword function globally available
   

    // Get form elements
    const userForm = document.getElementById('userForm');
    const firstName = document.getElementById('first_name');
    const lastName = document.getElementById('last_name');
    const email = document.getElementById('email');
    const phone = document.getElementById('phone');
    const roleSelect = document.getElementById('role_id');
    const userType = document.getElementById('user_type');
    
    // Password elements (for add form)
    const password = document.getElementById('password');
    const confirmPassword = document.getElementById('confirm_password');
    
    // Password elements (for edit form)
    const changePasswordCheckbox = document.getElementById('change_password');
    const newPassword = document.getElementById('new_password');
    const confirmNewPassword = document.getElementById('confirm_new_password');
    const passwordFields = document.getElementById('passwordFields');
    
    // ===== Phone number validation =====
    if (phone) {
        phone.addEventListener('input', function() {
            this.value = this.value.replace(/[^0-9]/g, '').slice(0, 10);
        });
    }

    // ===== Password Strength Checker (for add form) =====
    if (password && confirmPassword) {
        
        // Password strength requirements
        const reqLength = document.getElementById('req-length');
        const reqUppercase = document.getElementById('req-uppercase');
        const reqLowercase = document.getElementById('req-lowercase');
        const reqNumber = document.getElementById('req-number');
        const reqSpecial = document.getElementById('req-special');
        const reqMatch = document.getElementById('req-match');
        
        const passwordStrength = document.getElementById('passwordStrength');
        const passwordStrengthText = document.getElementById('passwordStrengthText');
        
        function checkPasswordStrength() {
            const pass = password.value;
            let strength = 0;
            
            // Check length
            if (pass.length >= 8) {
                reqLength.classList.add('valid');
                strength++;
            } else {
                reqLength.classList.remove('valid');
            }
            
            // Check uppercase
            if (/[A-Z]/.test(pass)) {
                reqUppercase.classList.add('valid');
                strength++;
            } else {
                reqUppercase.classList.remove('valid');
            }
            
            // Check lowercase
            if (/[a-z]/.test(pass)) {
                reqLowercase.classList.add('valid');
                strength++;
            } else {
                reqLowercase.classList.remove('valid');
            }
            
            // Check number
            if (/[0-9]/.test(pass)) {
                reqNumber.classList.add('valid');
                strength++;
            } else {
                reqNumber.classList.remove('valid');
            }
            
            // Check special character
            if (/[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]/.test(pass)) {
                reqSpecial.classList.add('valid');
                strength++;
            } else {
                reqSpecial.classList.remove('valid');
            }
            
            // Update strength meter
            const strengthPercent = (strength / 5) * 100;
            passwordStrength.style.width = strengthPercent + '%';
            
            if (strength <= 2) {
                passwordStrength.className = 'progress-bar bg-danger';
                passwordStrengthText.textContent = 'Weak password';
            } else if (strength <= 4) {
                passwordStrength.className = 'progress-bar bg-warning';
                passwordStrengthText.textContent = 'Medium password';
            } else {
                passwordStrength.className = 'progress-bar bg-success';
                passwordStrengthText.textContent = 'Strong password';
            }
        }
        
        function checkPasswordMatch() {
            if (confirmPassword.value) {
                if (password.value === confirmPassword.value) {
                    reqMatch.classList.add('valid');
                } else {
                    reqMatch.classList.remove('valid');
                }
            }
        }
        
        password.addEventListener('input', function() {
            checkPasswordStrength();
            checkPasswordMatch();
        });
        
        confirmPassword.addEventListener('input', checkPasswordMatch);
    }

    // ===== Toggle Password Fields (for edit form) =====
    if (changePasswordCheckbox && passwordFields) {
        changePasswordCheckbox.addEventListener('change', function() {
            if (this.checked) {
                passwordFields.style.display = 'block';
            } else {
                passwordFields.style.display = 'none';
                // Clear password fields
                if (newPassword) newPassword.value = '';
                if (confirmNewPassword) confirmNewPassword.value = '';
            }
        });
    }

    // ===== Preview Modal =====
    const previewBtn = document.getElementById('previewBtn');
    if (previewBtn) {
        previewBtn.addEventListener('click', function() {
            updatePreview();
            const previewModal = new bootstrap.Modal(document.getElementById('previewModal'));
            previewModal.show();
        });
    }

    // ===== Reset Button =====
    const resetBtn = document.getElementById('resetBtn');
    if (resetBtn) {
        resetBtn.addEventListener('click', function(e) {
            e.preventDefault();
            
            Swal.fire({
                icon: 'question',
                title: 'Reset Form',
                text: 'Are you sure you want to reset all fields?',
                showCancelButton: true,
                confirmButtonText: 'Yes, reset',
                cancelButtonText: 'Cancel',
                confirmButtonColor: '#8c0d4f',
                cancelButtonColor: '#6c757d'
            }).then((result) => {
                if (result.isConfirmed) {
                    userForm.reset();
                    
                    // Clear validation states
                    document.querySelectorAll('.form-control').forEach(input => {
                        input.classList.remove('is-invalid');
                    });
                    
                    // Reset password requirements
                    if (password && confirmPassword) {
                        document.querySelectorAll('.requirements-list li').forEach(li => {
                            li.classList.remove('valid');
                        });
                        passwordStrength.style.width = '0%';
                        passwordStrengthText.textContent = 'Enter password';
                    }
                    
                    // Hide password fields in edit form
                    if (passwordFields) {
                        passwordFields.style.display = 'none';
                    }
                }
            });
        });
    }

    // ===== Form Validation =====
    if (userForm) {
        userForm.addEventListener('submit', function(e) {
            if (!validateForm()) {
                e.preventDefault();
            }
        });
    }

    // ===== Helper Functions =====

    function validateForm() {
        const firstName = document.getElementById('first_name')?.value.trim();
        const email = document.getElementById('email')?.value.trim();
        const roleId = document.getElementById('role_id')?.value;
        
        let isValid = true;
        let errorMessage = '';
        
        if (!firstName) {
            errorMessage = 'First name is required';
            isValid = false;
        } else if (!email) {
            errorMessage = 'Email address is required';
            isValid = false;
        } else if (!roleId) {
            errorMessage = 'Please select a role';
            isValid = false;
        }
        
        // Password validation for add form
        if (password && confirmPassword) {
            const pass = password.value;
            const confirmPass = confirmPassword.value;
            
            if (!pass) {
                errorMessage = 'Password is required';
                isValid = false;
            } else if (pass.length < 8) {
                errorMessage = 'Password must be at least 8 characters';
                isValid = false;
            } else if (pass !== confirmPass) {
                errorMessage = 'Passwords do not match';
                isValid = false;
            }
        }
        
        // Password validation for edit form
        if (changePasswordCheckbox && changePasswordCheckbox.checked) {
            const newPass = newPassword?.value;
            const confirmNewPass = confirmNewPassword?.value;
            
            if (!newPass) {
                errorMessage = 'New password is required';
                isValid = false;
            } else if (newPass.length < 8) {
                errorMessage = 'Password must be at least 8 characters';
                isValid = false;
            } else if (newPass !== confirmNewPass) {
                errorMessage = 'Passwords do not match';
                isValid = false;
            }
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

    function updatePreview() {
        const firstName = document.getElementById('first_name')?.value.trim() || '';
        const lastName = document.getElementById('last_name')?.value.trim() || '';
        const fullName = firstName + (lastName ? ' ' + lastName : '');
        const email = document.getElementById('email')?.value || '-';
        const phone = document.getElementById('phone')?.value || '-';
        const roleSelect = document.getElementById('role_id');
        const role = roleSelect ? roleSelect.options[roleSelect.selectedIndex]?.text || '-' : '-';
        const userType = document.getElementById('user_type')?.value || 'guest';
        const isActive = document.getElementById('isActive')?.checked || false;
        
        // Update preview
        document.getElementById('previewName').textContent = fullName || '-';
        document.getElementById('previewEmail').textContent = email;
        document.getElementById('previewPhone').textContent = phone || '-';
        document.getElementById('previewRole').textContent = role;
        document.getElementById('previewType').textContent = userType.charAt(0).toUpperCase() + userType.slice(1);
        document.getElementById('previewStatus').textContent = isActive ? 'Active' : 'Inactive';
        
        // Update avatar
        const previewAvatar = document.getElementById('previewAvatar');
        if (previewAvatar) {
            previewAvatar.textContent = firstName.charAt(0).toUpperCase() || email.charAt(0).toUpperCase();
        }
    }
});