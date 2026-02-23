// static/js/masters/user-list.js

document.addEventListener('DOMContentLoaded', function() {
    
    // ===== Delete User Functionality =====
    const deleteButtons = document.querySelectorAll('.delete-btn');
    const deleteModal = document.getElementById('deleteUserModal');
    const deleteUserName = document.getElementById('deleteUserName');
    const deleteUserId = document.getElementById('deleteUserId');
    
    if (deleteButtons.length > 0 && deleteModal) {
        const modal = new bootstrap.Modal(deleteModal);
        
        deleteButtons.forEach(button => {
            button.addEventListener('click', function() {
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
        });
    }

    // ===== Status Toggle Functionality =====
    const statusSwitches = document.querySelectorAll('.status-switch');
    
    statusSwitches.forEach(switch_ => {
        switch_.addEventListener('change', function() {
            const userId = this.dataset.userId;
            const userEmail = this.dataset.userEmail;
            const isActive = this.checked;
            const originalState = !isActive;
            
            // Show loading state
            this.disabled = true;
            
            // Send AJAX request to toggle status
            fetch('/toggle_user_status/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: new URLSearchParams({
                    'user_id': userId
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Update switch state
                    this.checked = data.is_active;
                    
                    // Update label
                    const label = this.closest('.status-toggle').querySelector('.form-check-label');
                    if (label) {
                        label.textContent = data.is_active ? 'Active' : 'Inactive';
                    }
                    
                    // Show success message
                    Swal.fire({
                        icon: 'success',
                        title: 'Success',
                        text: data.message,
                        timer: 2000,
                        showConfirmButton: false
                    });
                } else {
                    // Revert switch
                    this.checked = originalState;
                    
                    // Show error message
                    Swal.fire({
                        icon: 'error',
                        title: 'Error',
                        text: data.message
                    });
                }
            })
            .catch(error => {
                console.error('Error:', error);
                this.checked = originalState;
                Swal.fire({
                    icon: 'error',
                    title: 'Error',
                    text: 'Something went wrong. Please try again.'
                });
            })
            .finally(() => {
                this.disabled = false;
            });
        });
    });

    // ===== Search and Filter Functionality =====
    const searchInput = document.getElementById('searchUser');
    const filterRole = document.getElementById('filterRole');
    const filterStatus = document.getElementById('filterStatus');
    const resetBtn = document.getElementById('resetFilters');
    const clearSearch = document.getElementById('clearSearch');
    const tableBody = document.getElementById('usersTableBody');
    const rows = tableBody ? tableBody.getElementsByTagName('tr') : [];

    console.log('Filter elements found:', { 
        searchInput: !!searchInput, 
        filterRole: !!filterRole, 
        filterStatus: !!filterStatus,
        rowsCount: rows.length 
    });

    if (searchInput && filterRole && filterStatus) {
        
        function filterTable() {
            const searchTerm = searchInput.value.toLowerCase().trim();
            const roleFilter = filterRole.value; // This is role ID
            const statusFilter = filterStatus.value; // 'active' or 'inactive'
            
            console.log('Filtering with:', { searchTerm, roleFilter, statusFilter });
            
            let visibleCount = 0;
            
            Array.from(rows).forEach((row, index) => {
                // Skip empty state row
                if (row.querySelector('.empty-state')) return;
                
                // Get cell data with proper indexing
                const nameCell = row.cells[1]; // User column
                const roleCell = row.cells[3]; // Role column
                const statusCell = row.cells[6]; // Status/Actions column
                
                if (!nameCell || !roleCell || !statusCell) {
                    console.log('Missing cells for row', index);
                    return;
                }
                
                // Get user name and email from the user-info-cell
                const userInfoDiv = nameCell.querySelector('.user-details');
                const userName = userInfoDiv ? userInfoDiv.querySelector('strong')?.textContent.toLowerCase() || '' : '';
                const userEmail = userInfoDiv ? userInfoDiv.querySelector('small')?.textContent.toLowerCase() || '' : '';
                
                // Get role text
                const roleText = roleCell.textContent.trim();
                
                // Get status
                const statusSwitch = statusCell.querySelector('.status-switch');
                const superuserBadge = statusCell.querySelector('.status-superuser');
                
                let isActive = false;
                if (statusSwitch) {
                    isActive = statusSwitch.checked;
                }
                
                console.log(`Row ${index}:`, {
                    userName,
                    userEmail,
                    roleText,
                    isActive,
                    hasSuperuser: !!superuserBadge
                });
                
                let matchesSearch = true;
                let matchesRole = true;
                let matchesStatus = true;
                
                // Search filter - search in name and email
                if (searchTerm) {
                    matchesSearch = userName.includes(searchTerm) || 
                                   userEmail.includes(searchTerm);
                }
                
                // Role filter - match by role ID
                if (roleFilter) {
                    // Get the role ID from the role name
                    const roleOption = Array.from(filterRole.options).find(opt => opt.text === roleText);
                    if (roleOption) {
                        matchesRole = roleOption.value === roleFilter;
                    } else {
                        matchesRole = false;
                    }
                }
                
                // Status filter
                if (statusFilter) {
                    if (superuserBadge) {
                        // Superusers don't match active/inactive filters
                        matchesStatus = false;
                    } else {
                        if (statusFilter === 'active') {
                            matchesStatus = isActive === true;
                        } else if (statusFilter === 'inactive') {
                            matchesStatus = isActive === false;
                        }
                    }
                }
                
                // Show/hide row
                if (matchesSearch && matchesRole && matchesStatus) {
                    row.style.display = '';
                    visibleCount++;
                } else {
                    row.style.display = 'none';
                }
            });
            
            console.log('Visible rows:', visibleCount);
            
            // Show/hide clear search button
            if (searchTerm) {
                clearSearch.style.display = 'block';
            } else {
                clearSearch.style.display = 'none';
            }
            
            // Optional: Show "no results" message
            if (visibleCount === 0) {
                // You could show a "No matching users" row here
                console.log('No matching users found');
            }
        }
        
        // Event listeners
        searchInput.addEventListener('keyup', filterTable);
        filterRole.addEventListener('change', function() {
            console.log('Role filter changed to:', this.value);
            filterTable();
        });
        filterStatus.addEventListener('change', function() {
            console.log('Status filter changed to:', this.value);
            filterTable();
        });
        
        // Clear search
        if (clearSearch) {
            clearSearch.addEventListener('click', function() {
                searchInput.value = '';
                clearSearch.style.display = 'none';
                filterTable();
            });
        }
        
        // Reset filters
        if (resetBtn) {
            resetBtn.addEventListener('click', function() {
                searchInput.value = '';
                filterRole.value = '';
                filterStatus.value = '';
                clearSearch.style.display = 'none';
                filterTable();
            });
        }
    } else {
        console.error('Filter elements not found!');
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
});