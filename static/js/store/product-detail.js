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