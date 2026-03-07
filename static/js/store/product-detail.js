// static/js/product-detail.js

document.addEventListener('DOMContentLoaded', function() {
    
    // Initialize quantity input
    const quantityInput = document.getElementById('quantity');
    if (quantityInput) {
        // Prevent manual entry of invalid values
        quantityInput.addEventListener('change', function() {
            let value = parseInt(this.value);
            const min = parseInt(this.getAttribute('min')) || 1;
            const max = parseInt(this.getAttribute('max')) || 10;
            
            if (isNaN(value) || value < min) {
                this.value = min;
            } else if (value > max) {
                this.value = max;
            }
        });
    }
    
    // Image zoom effect (optional)
    const mainImage = document.getElementById('mainProductImage');
    if (mainImage) {
        mainImage.addEventListener('mousemove', function(e) {
            const { left, top, width, height } = this.getBoundingClientRect();
            const x = (e.clientX - left) / width * 100;
            const y = (e.clientY - top) / height * 100;
            this.style.transformOrigin = `${x}% ${y}%`;
        });
        
        mainImage.addEventListener('mouseleave', function() {
            this.style.transformOrigin = 'center';
        });
    }
    
    // Add to cart animation
    const addToCartBtn = document.querySelector('.btn-add-to-cart');
    if (addToCartBtn) {
        addToCartBtn.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Add animation class
            this.classList.add('clicked');
            
            // Remove class after animation
            setTimeout(() => {
                this.classList.remove('clicked');
            }, 300);
        });
    }
    
    // Wishlist button animation
    const wishlistBtn = document.querySelector('.btn-wishlist');
    if (wishlistBtn) {
        wishlistBtn.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Toggle heart icon
            const icon = this.querySelector('i');
            if (icon.classList.contains('bi-heart')) {
                icon.classList.remove('bi-heart');
                icon.classList.add('bi-heart-fill');
                this.style.background = 'var(--accent-color)';
                this.style.color = 'white';
            } else {
                icon.classList.remove('bi-heart-fill');
                icon.classList.add('bi-heart');
                this.style.background = 'white';
                this.style.color = 'var(--accent-color)';
            }
            
            // Add pulse animation
            this.style.animation = 'pulse 0.5s ease';
            setTimeout(() => {
                this.style.animation = '';
            }, 500);
        });
    }
});

// Add pulse animation
const style = document.createElement('style');
style.textContent = `
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.1); }
        100% { transform: scale(1); }
    }
    
    .btn-add-to-cart.clicked {
        animation: pulse 0.3s ease;
    }
`;
document.head.appendChild(style);

// Star rating functionality
document.addEventListener('DOMContentLoaded', function() {
    const stars = document.querySelectorAll('.star-rating i');
    const ratingInput = document.getElementById('selectedRating');
    
    if (stars.length) {
        stars.forEach(star => {
            star.addEventListener('mouseenter', function() {
                const rating = this.dataset.rating;
                highlightStars(rating);
            });
            
            star.addEventListener('mouseleave', function() {
                const currentRating = ratingInput.value;
                if (currentRating) {
                    highlightStars(currentRating);
                } else {
                    resetStars();
                }
            });
            
            star.addEventListener('click', function() {
                const rating = this.dataset.rating;
                ratingInput.value = rating;
                highlightStars(rating);
            });
        });
    }
    
    // Character count for review
    const reviewTextarea = document.getElementById('reviewComment');
    const charCount = document.getElementById('charCount');
    
    if (reviewTextarea && charCount) {
        reviewTextarea.addEventListener('input', function() {
            const count = this.value.length;
            charCount.textContent = count;
            
            if (count >= 500) {
                charCount.style.color = '#dc3545';
            } else {
                charCount.style.color = 'var(--accent-color)';
            }
        });
    }
    
    // Review form submission with SweetAlert
    const reviewForm = document.getElementById('reviewForm');
    if (reviewForm) {
        reviewForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Validate rating
            if (!ratingInput.value) {
                Swal.fire({
                    icon: 'error',
                    title: 'Rating Required',
                    text: 'Please select a star rating',
                    confirmButtonColor: '#8c0d4f'
                });
                return;
            }
            
            // Validate comment
            const comment = reviewTextarea.value.trim();
            if (!comment) {
                Swal.fire({
                    icon: 'error',
                    title: 'Review Required',
                    text: 'Please write your review',
                    confirmButtonColor: '#8c0d4f'
                });
                return;
            }
            
            if (comment.length < 10) {
                Swal.fire({
                    icon: 'error',
                    title: 'Review Too Short',
                    text: 'Please write at least 10 characters',
                    confirmButtonColor: '#8c0d4f'
                });
                return;
            }
            
            // Show loading
            Swal.fire({
                title: 'Submitting...',
                text: 'Please wait',
                allowOutsideClick: false,
                didOpen: () => {
                    Swal.showLoading();
                }
            });
            
            // Submit form
            const formData = new FormData(this);
            
            fetch(this.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    Swal.fire({
                        icon: 'success',
                        title: 'Review Submitted!',
                        text: data.message,
                        confirmButtonColor: '#8c0d4f'
                    }).then(() => {
                        location.reload();
                    });
                } else {
                    Swal.fire({
                        icon: 'error',
                        title: 'Error',
                        text: data.message,
                        confirmButtonColor: '#8c0d4f'
                    });
                }
            })
            .catch(error => {
                Swal.fire({
                    icon: 'error',
                    title: 'Error',
                    text: 'Something went wrong',
                    confirmButtonColor: '#8c0d4f'
                });
            });
        });
    }
});

function highlightStars(rating) {
    const stars = document.querySelectorAll('.star-rating i');
    stars.forEach((star, index) => {
        if (index < rating) {
            star.classList.remove('bi-star');
            star.classList.add('bi-star-fill');
        } else {
            star.classList.remove('bi-star-fill');
            star.classList.add('bi-star');
        }
    });
}

function resetStars() {
    const stars = document.querySelectorAll('.star-rating i');
    stars.forEach(star => {
        star.classList.remove('bi-star-fill');
        star.classList.add('bi-star');
    });
}

// Sticky Header on Scroll
document.addEventListener('DOMContentLoaded', function() {
    const stickyHeader = document.getElementById('stickyProductHeader');
    const mainProductSection = document.querySelector('.product-main');
    const mainQuantity = document.getElementById('quantity');
    const stickyQuantity = document.getElementById('stickyQuantity');
    
    if (stickyHeader && mainProductSection) {
        // Get the offset position of the main product section
        const mainSectionBottom = mainProductSection.offsetTop + mainProductSection.offsetHeight;
        
        window.addEventListener('scroll', function() {
            if (window.scrollY > mainSectionBottom - 100) {
                stickyHeader.classList.add('show');
                document.body.classList.add('has-sticky-header');
            } else {
                stickyHeader.classList.remove('show');
                document.body.classList.remove('has-sticky-header');
            }
        });
    }
    
    // Sync quantities between main and sticky
    if (mainQuantity && stickyQuantity) {
        // Update sticky quantity when main changes
        mainQuantity.addEventListener('input', function() {
            stickyQuantity.value = this.value;
        });
        
        // Update main quantity when sticky changes
        stickyQuantity.addEventListener('input', function() {
            mainQuantity.value = this.value;
        });
    }
});

// Sticky quantity controls
function incrementStickyQuantity() {
    const input = document.getElementById('stickyQuantity');
    const mainInput = document.getElementById('quantity');
    const max = parseInt(input.getAttribute('max')) || 10;
    let value = parseInt(input.value) || 1;
    
    if (value < max) {
        input.value = value + 1;
        if (mainInput) mainInput.value = value + 1;
    }
}

function decrementStickyQuantity() {
    const input = document.getElementById('stickyQuantity');
    const mainInput = document.getElementById('quantity');
    let value = parseInt(input.value) || 1;
    
    if (value > 1) {
        input.value = value - 1;
        if (mainInput) mainInput.value = value - 1;
    }
}

// Add to cart from sticky header
function addToCartFromSticky(encryptedId) {
    const quantity = document.getElementById('stickyQuantity').value;
    addToCart(encryptedId, quantity);
}

// Update your existing addToCart function to handle the call
function addToCart(encryptedId, quantity) {
    // Your existing add to cart logic
    console.log('Adding to cart:', encryptedId, 'Quantity:', quantity);
    Swal.fire({
        icon: 'success',
        title: 'Added to Cart!',
        text: 'Product has been added to your cart.',
        showConfirmButton: false,
        timer: 1500
    });
}