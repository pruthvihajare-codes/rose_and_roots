// static/js/masters/user-view.js

document.addEventListener('DOMContentLoaded', function() {
    
    // ===== Delete User Functionality =====
    const deleteButton = document.querySelector('.btn-delete');
    const deleteModal = document.getElementById('deleteUserModal');
    const deleteUserName = document.getElementById('deleteUserName');
    const deleteUserId = document.getElementById('deleteUserId');
    
    if (deleteButton && deleteModal) {
        const modal = new bootstrap.Modal(deleteModal);
        
        deleteButton.addEventListener('click', function() {
            const userId = this.dataset.userId;
            const userName = this.dataset.userName;
            
            if (deleteUserName) {
                deleteUserName.textContent = userName;
            }
            
            if (deleteUserId) {
                deleteUserId.value = userId;
            }
            
            modal.show();
        });
    }
});