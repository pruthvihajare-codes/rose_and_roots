// static/js/masters/bouquet-edit.js

document.addEventListener('DOMContentLoaded', function() {
    
    // ===== Occasion Selector =====
    const occasionCards = document.querySelectorAll('.occasion-card');
    const selectedOccasionsInput = document.getElementById('selected_occasions_input');
    const previewContainer = document.getElementById('selectedOccasionsPreview');
    
    if (occasionCards.length) {
        // Initialize selected state
        let selectedIds = selectedOccasionsInput.value ? selectedOccasionsInput.value.split(',') : [];
        
        // Mark cards as selected based on hidden input
        occasionCards.forEach(card => {
            const cardId = card.dataset.id;
            if (selectedIds.includes(cardId)) {
                card.classList.add('selected');
            }
        });
        
        // Add click handlers
        occasionCards.forEach(card => {
            card.addEventListener('click', function(e) {
                e.preventDefault();
                toggleOccasion(this);
            });
        });
        
        // Update preview initially
        updatePreviewFromSelected(selectedIds);
    }
    
    function toggleOccasion(card) {
        const occasionId = card.dataset.id;
        const occasionName = card.dataset.name;
        
        // Toggle selected class
        card.classList.toggle('selected');
        
        // Get current selected IDs
        let selectedIds = selectedOccasionsInput.value ? 
            selectedOccasionsInput.value.split(',').filter(id => id) : [];
        
        if (card.classList.contains('selected')) {
            // Add to selection
            if (!selectedIds.includes(occasionId)) {
                selectedIds.push(occasionId);
            }
            addPreviewTag(occasionId, occasionName);
        } else {
            // Remove from selection
            selectedIds = selectedIds.filter(id => id !== occasionId);
            removePreviewTag(occasionId);
        }
        
        // Update hidden input
        selectedOccasionsInput.value = selectedIds.join(',');
        
        // Show/hide placeholder
        togglePlaceholder(selectedIds.length === 0);
    }
    
    function addPreviewTag(id, name) {
        const placeholder = previewContainer.querySelector('.preview-placeholder');
        
        // Hide placeholder
        if (placeholder) placeholder.classList.add('d-none');
        
        // Check if tag already exists
        if (previewContainer.querySelector(`.preview-tag[data-id="${id}"]`)) {
            return;
        }
        
        // Create new tag
        const tag = document.createElement('span');
        tag.className = 'preview-tag';
        tag.dataset.id = id;
        tag.innerHTML = `
            <i class="bi bi-check-circle-fill"></i>
            ${name}
            <i class="bi bi-x-circle-fill" onclick="removeOccasion('${id}', event)"></i>
        `;
        
        previewContainer.appendChild(tag);
    }
    
    function removePreviewTag(id) {
        const tag = previewContainer.querySelector(`.preview-tag[data-id="${id}"]`);
        if (tag) {
            tag.remove();
            togglePlaceholder();
        }
    }
    
    function togglePlaceholder(force) {
        const placeholder = previewContainer.querySelector('.preview-placeholder');
        const tags = previewContainer.querySelectorAll('.preview-tag');
        
        if (placeholder) {
            if (tags.length === 0 || force === true) {
                placeholder.classList.remove('d-none');
            } else {
                placeholder.classList.add('d-none');
            }
        }
    }
    
    function updatePreviewFromSelected(selectedIds) {
        if (!selectedIds || selectedIds.length === 0) {
            togglePlaceholder(true);
            return;
        }
        
        // Clear existing preview tags
        const existingTags = previewContainer.querySelectorAll('.preview-tag');
        existingTags.forEach(tag => tag.remove());
        
        // Add tags for each selected ID
        selectedIds.forEach(id => {
            const card = document.querySelector(`.occasion-card[data-id="${id}"]`);
            if (card) {
                const name = card.dataset.name;
                addPreviewTag(id, name);
            }
        });
    }

    // ===== Image Upload =====
    let dataTransfer = new DataTransfer();
    const uploadArea = document.getElementById('imageUploadArea');
    const imageInput = document.getElementById('bouquet_images');
    const previewGrid = document.getElementById('imagePreviewGrid');
    
    const MAX_IMAGES = 5;
    const MAX_FILE_SIZE = 6 * 1024 * 1024;
    const ALLOWED_TYPES = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'image/gif'];
    
    if (uploadArea && imageInput) {
        // Get current image count
        const currentImages = document.querySelectorAll('.current-image-item').length;
        
        // Add image count indicator
        addImageCountIndicator(0, MAX_IMAGES - currentImages);
        
        // Prevent defaults for drag events
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, preventDefaults, false);
        });
        
        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }
        
        // Add dragover effect
        ['dragenter', 'dragover'].forEach(eventName => {
            uploadArea.addEventListener(eventName, () => {
                uploadArea.classList.add('dragover');
            });
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, () => {
                uploadArea.classList.remove('dragover');
            });
        });
        
        // Handle drop event
        uploadArea.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            validateAndProcessFiles(files);
        });
        
        // Handle file input change
        imageInput.addEventListener('change', (e) => {
            validateAndProcessFiles(e.target.files);
        });
        
        // Browse button click
        const browseBtn = document.querySelector('.btn-browse');
        if (browseBtn) {
            browseBtn.addEventListener('click', function(e) {
                e.preventDefault();
                imageInput.click();
            });
        }
        
        function validateAndProcessFiles(files) {
            if (!files || files.length === 0) return;
            
            const currentImages = document.querySelectorAll('.current-image-item').length;
            const newPreviews = previewGrid.querySelectorAll('.preview-item').length;
            const totalAfterAdd = currentImages + newPreviews + files.length;
            
            if (totalAfterAdd > MAX_IMAGES) {
                showUploadError(`You can only have maximum ${MAX_IMAGES} images total. You can add ${MAX_IMAGES - (currentImages + newPreviews)} more.`);
                return;
            }
            
            const fileArray = Array.from(files);
            let validFiles = [];
            let errors = [];
            
            fileArray.forEach(file => {
                const isValidType = ALLOWED_TYPES.includes(file.type);
                
                if (!isValidType) {
                    errors.push(`"${file.name}" is not a valid image file.`);
                    return;
                }
                
                if (file.size > MAX_FILE_SIZE) {
                    errors.push(`"${file.name}" exceeds 6MB limit.`);
                    return;
                }
                
                validFiles.push(file);
                dataTransfer.items.add(file);
            });
            
            if (errors.length > 0) {
                showUploadError(errors.join('<br>'));
            }
            
            if (validFiles.length > 0) {
                processImageFiles(validFiles);
                imageInput.files = dataTransfer.files;
            }
        }
        
        function processImageFiles(files) {
            files.forEach(file => {
                const reader = new FileReader();
                
                reader.onload = (e) => {
                    const previewItem = createPreviewItem(e.target.result, file.name);
                    previewGrid.appendChild(previewItem);
                    
                    const currentImages = document.querySelectorAll('.current-image-item').length;
                    const newPreviews = previewGrid.querySelectorAll('.preview-item').length;
                    updateImageCount(newPreviews, MAX_IMAGES - currentImages);
                };
                
                reader.readAsDataURL(file);
            });
        }
        
        function createPreviewItem(imageSrc, fileName) {
            const previewItem = document.createElement('div');
            previewItem.className = 'preview-item';
            
            const displayName = fileName.length > 15 ? fileName.substring(0, 12) + '...' : fileName;
            
            previewItem.innerHTML = `
                <img src="${imageSrc}" alt="Preview">
                <div class="preview-info">
                    <span class="preview-filename" title="${fileName}">${displayName}</span>
                </div>
                <button type="button" class="preview-remove" onclick="removeNewImage(this, '${fileName}')">
                    <i class="bi bi-x"></i>
                </button>
            `;
            
            return previewItem;
        }
    }
    
    function addImageCountIndicator(currentCount, remaining) {
        const formGroup = document.querySelector('.image-upload-area')?.closest('.form-section');
        if (!formGroup) return;
        
        const existingIndicator = document.querySelector('.image-count-indicator');
        if (existingIndicator) existingIndicator.remove();
        
        const countIndicator = document.createElement('div');
        countIndicator.className = 'image-count-indicator';
        countIndicator.innerHTML = `
            <span class="image-count-text">
                <i class="bi bi-images"></i>
                <span id="imageCount">${currentCount}</span> new images
            </span>
            <span class="image-count-limit" id="imageCountLimit">
                ${remaining} slots remaining
            </span>
        `;
        
        formGroup.insertBefore(countIndicator, document.querySelector('.image-preview-grid'));
    }
    
    function updateImageCount(count, remaining) {
        const imageCountSpan = document.getElementById('imageCount');
        const imageCountLimit = document.getElementById('imageCountLimit');
        
        if (imageCountSpan) {
            imageCountSpan.textContent = count;
        }
        
        if (imageCountLimit) {
            imageCountLimit.textContent = `${remaining} slots remaining`;
        }
    }
    
    function showUploadError(message) {
        removeUploadError();
        
        const uploadArea = document.getElementById('imageUploadArea');
        if (!uploadArea) return;
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'upload-error-message';
        errorDiv.id = 'uploadErrorMessage';
        errorDiv.innerHTML = `
            <i class="bi bi-exclamation-triangle-fill"></i>
            <span>${message}</span>
        `;
        
        uploadArea.parentNode.insertBefore(errorDiv, uploadArea.nextSibling);
        
        setTimeout(() => {
            const error = document.getElementById('uploadErrorMessage');
            if (error) {
                error.style.animation = 'fadeOut 0.3s ease';
                setTimeout(() => error.remove(), 300);
            }
        }, 5000);
    }
    
    function removeUploadError() {
        const existingError = document.getElementById('uploadErrorMessage');
        if (existingError) {
            existingError.remove();
        }
    }

    // ===== Form Submission =====
    const bouquetForm = document.getElementById('bouquetForm');
    
    if (bouquetForm) {
        bouquetForm.addEventListener('submit', function(e) {
            const selectedOccasions = selectedOccasionsInput.value;
            const currentImages = document.querySelectorAll('.current-image-item').length;
            const newImages = previewGrid.querySelectorAll('.preview-item').length;
            
            if (!selectedOccasions) {
                e.preventDefault();
                Swal.fire({
                    icon: 'error',
                    title: 'Validation Error',
                    text: 'Please select at least one occasion',
                    confirmButtonColor: '#8c0d4f'
                });
                return false;
            }
            
            if (currentImages + newImages === 0) {
                e.preventDefault();
                Swal.fire({
                    icon: 'error',
                    title: 'Validation Error',
                    text: 'Please upload at least one image',
                    confirmButtonColor: '#8c0d4f'
                });
                return false;
            }
        });
    }
});

// Global functions
function removeOccasion(id, event) {
    if (event) {
        event.stopPropagation();
    }
    
    const card = document.querySelector(`.occasion-card[data-id="${id}"]`);
    if (card) {
        card.classList.remove('selected');
    }
    
    const selectedOccasionsInput = document.getElementById('selected_occasions_input');
    let selectedIds = selectedOccasionsInput.value ? 
        selectedOccasionsInput.value.split(',').filter(pid => pid !== id) : [];
    selectedOccasionsInput.value = selectedIds.join(',');
    
    const tag = document.querySelector(`.preview-tag[data-id="${id}"]`);
    if (tag) {
        tag.remove();
    }
    
    const placeholder = document.querySelector('.preview-placeholder');
    const tags = document.querySelectorAll('.preview-tag');
    if (placeholder && tags.length === 0) {
        placeholder.classList.remove('d-none');
    }
}

function removeNewImage(button, fileName) {
    const previewItem = button.closest('.preview-item');
    const previewGrid = document.getElementById('imagePreviewGrid');
    const imageInput = document.getElementById('bouquet_images');
    
    if (previewItem) {
        previewItem.remove();
        
        let dt = new DataTransfer();
        let files = imageInput.files;
        
        for (let i = 0; i < files.length; i++) {
            if (files[i].name !== fileName) {
                dt.items.add(files[i]);
            }
        }
        
        imageInput.files = dt.files;
        
        const currentImages = document.querySelectorAll('.current-image-item').length;
        const newPreviews = previewGrid.querySelectorAll('.preview-item').length;
        const remaining = 5 - (currentImages + newPreviews);
        
        const imageCountSpan = document.getElementById('imageCount');
        const imageCountLimit = document.getElementById('imageCountLimit');
        
        if (imageCountSpan) {
            imageCountSpan.textContent = newPreviews;
        }
        
        if (imageCountLimit) {
            imageCountLimit.textContent = `${remaining} slots remaining`;
        }
    }
}