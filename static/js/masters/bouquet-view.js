// static/js/masters/bouquet-view.js

document.addEventListener('DOMContentLoaded', function() {
    
    // ===== Delete Bouquet Functionality =====
    const deleteButton = document.querySelector('.btn-delete');
    const deleteModal = document.getElementById('deleteBouquetModal');
    const deleteBouquetName = document.getElementById('deleteBouquetName');
    const deleteBouquetId = document.getElementById('deleteBouquetId');
    
    if (deleteButton && deleteModal) {
        const modal = new bootstrap.Modal(deleteModal);
        
        deleteButton.addEventListener('click', function() {
            const bouquetId = this.dataset.bouquetId;
            const bouquetName = this.dataset.bouquetName;
            
            if (deleteBouquetName) {
                deleteBouquetName.textContent = bouquetName;
            }
            
            if (deleteBouquetId) {
                deleteBouquetId.value = bouquetId;
            }
            
            modal.show();
        });
    }

    // ===== Image Gallery Lightbox =====
    const galleryItems = document.querySelectorAll('.gallery-item');
    
    galleryItems.forEach(item => {
        item.addEventListener('click', function() {
            const img = this.querySelector('img');
            if (img) {
                openLightbox(img.src);
            }
        });
    });

    // ===== SweetAlert for Messages =====
    function showAlert(type, message) {
        Swal.fire({
            icon: type,
            title: type === 'success' ? 'Success' : type === 'error' ? 'Error' : 'Info',
            text: message,
            confirmButtonText: 'OK',
            background: "#ffffff",
            color: "#343a40",
            confirmButtonColor: "#8c0d4f",
            customClass: {
                popup: 'rounded-4 shadow'
            }
        });
    }
});

// Lightbox function (global)
function openLightbox(imageSrc) {
    const lightboxModal = new bootstrap.Modal(document.getElementById('lightboxModal'));
    document.getElementById('lightboxImage').src = imageSrc;
    lightboxModal.show();
}