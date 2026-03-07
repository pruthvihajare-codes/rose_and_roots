// static/js/store/cart.js

document.addEventListener('DOMContentLoaded', function() {
    
    // Initialize cart
    initializeCart();
    
    // Setup delete confirmation
    setupDeleteConfirmation();
});

function initializeCart() {
    // Any initialization code
    console.log('Cart initialized');
}

function setupDeleteConfirmation() {
    // This is handled by the removeFromCart function
}

// Helper function to get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Remove from cart function with SweetAlert confirmation
function removeFromCart(encryptedId) {
    console.log('removeFromCart called with ID:', encryptedId);
    debugger;
    // Show confirmation dialog
    Swal.fire({
        title: 'Remove Item?',
        text: 'Are you sure you want to remove this item from your cart?',
        icon: 'question',
        showCancelButton: true,
        confirmButtonColor: '#dc3545',
        cancelButtonColor: '#6c757d',
        confirmButtonText: 'Yes, remove it!',
        cancelButtonText: 'Cancel'
    }).then((result) => {
        if (result.isConfirmed) {
            console.log('User confirmed, proceeding with removal');
            performRemoveFromCart(encryptedId);
        } else {
            console.log('User cancelled removal');
        }
    });
}

// Actual removal function
function performRemoveFromCart(encryptedId) {
    // Get the cart item element
    const cartItem = document.querySelector(`.cart-item[data-id="${encryptedId}"]`);
    
    // Show loading state on the remove button
    const removeBtn = cartItem ? cartItem.querySelector('.btn-remove-item') : null;
    const originalBtnHtml = removeBtn ? removeBtn.innerHTML : '';
    
    if (removeBtn) {
        removeBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';
        removeBtn.disabled = true;
    }
    
    // Get CSRF token
    const csrftoken = getCookie('csrftoken');
    
    // AJAX request to remove item
    $.ajax({
        url: '/remove_from_cart',
        type: 'POST',
        headers: {
            'X-CSRFToken': csrftoken
        },
        data: JSON.stringify({
            bouquet_id: encryptedId
        }),
        contentType: 'application/json',
        success: function(data) {
            if (data.success) {
                // Show success message
                Swal.fire({
                    icon: 'success',
                    title: 'Removed!',
                    text: 'Item has been removed from your cart.',
                    showConfirmButton: false,
                    timer: 1500,
                    background: "#ffffff",
                    confirmButtonColor: "#8c0d4f",
                    customClass: {
                        popup: 'rounded-4 shadow'
                    }
                });
                
                // Remove item from DOM with animation
                if (cartItem) {
                    cartItem.style.transition = 'all 0.3s ease';
                    cartItem.style.opacity = '0';
                    cartItem.style.transform = 'translateX(50px)';
                    
                    setTimeout(() => {
                        cartItem.remove();
                        
                        // Update cart summary
                        updateCartSummary(data);
                        
                        // Update cart badge
                        if (typeof updateCartBadge === 'function') {
                            updateCartBadge(data.cart_count);
                        }
                        
                        // Check if cart is empty and reload if needed
                        checkEmptyCart();
                    }, 300);
                } else {
                    // If item element not found, just reload the page
                    location.reload();
                }
            } else {
                // Show error message
                Swal.fire({
                    icon: 'error',
                    title: 'Error',
                    text: data.message || 'Could not remove item',
                    confirmButtonColor: "#8c0d4f",
                    background: "#ffffff",
                    customClass: {
                        popup: 'rounded-4 shadow'
                    }
                });
                
                // Restore button
                if (removeBtn) {
                    removeBtn.innerHTML = originalBtnHtml;
                    removeBtn.disabled = false;
                }
            }
        },
        error: function(xhr, status, error) {
            console.error('Error removing item:', error);
            
            // Show error message
            Swal.fire({
                icon: 'error',
                title: 'Error',
                text: 'Could not remove item. Please try again.',
                confirmButtonColor: "#8c0d4f",
                background: "#ffffff",
                customClass: {
                    popup: 'rounded-4 shadow'
                }
            });
            
            // Restore button
            if (removeBtn) {
                removeBtn.innerHTML = originalBtnHtml;
                removeBtn.disabled = false;
            }
        }
    });
}

// Update cart summary after removal
function updateCartSummary(data) {
    // Update item count display
    const itemCountElements = document.querySelectorAll('.cart-subtitle, .summary-row span:first-child');
    itemCountElements.forEach(el => {
        if (el.textContent.includes('item')) {
            const newText = `You have ${data.cart_count} item${data.cart_count !== 1 ? 's' : ''} in your cart`;
            if (el.closest('.cart-subtitle')) {
                el.textContent = newText;
            }
        }
    });
    
    // Update summary numbers
    const subtotalEl = document.querySelector('.summary-row span:last-child');
    const shippingEl = document.querySelectorAll('.summary-row span')[3]; // Adjust selector as needed
    const totalEl = document.querySelector('.total-amount');
    
    if (data.cart_total !== undefined) {
        if (subtotalEl) subtotalEl.textContent = '₹' + data.cart_total.toFixed(0);
        if (totalEl) totalEl.textContent = '₹' + data.cart_total.toFixed(0);
    }
    
    // Update remaining slots
    const limitCountEl = document.querySelector('.limit-count');
    if (limitCountEl && data.remaining_slots !== undefined) {
        const currentCount = parseInt(limitCountEl.textContent.split('/')[0]);
        limitCountEl.textContent = `${currentCount - 1}/10`;
        
        // Update progress bar
        const progressBar = document.querySelector('.limit-progress .progress-bar');
        if (progressBar) {
            const newPercentage = ((currentCount - 1) / 10) * 100;
            progressBar.style.width = newPercentage + '%';
            progressBar.setAttribute('aria-valuenow', currentCount - 1);
        }
    }
}

// Check if cart is empty
function checkEmptyCart() {
    const cartItems = document.querySelectorAll('.cart-item');
    if (cartItems.length === 0) {
        // Reload to show empty cart state
        setTimeout(() => {
            location.reload();
        }, 500);
    }
}

// Make functions globally available
window.removeFromCart = removeFromCart;