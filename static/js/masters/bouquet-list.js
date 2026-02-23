// static/js/masters/bouquet-list.js

document.addEventListener('DOMContentLoaded', function() {
    
    // ===== Delete Bouquet Functionality =====
    const deleteButtons = document.querySelectorAll('.delete-btn');
    const deleteModal = document.getElementById('deleteBouquetModal');
    const deleteBouquetName = document.getElementById('deleteBouquetName');
    const deleteBouquetId = document.getElementById('deleteBouquetId');
    
    if (deleteButtons.length > 0 && deleteModal) {
        const modal = new bootstrap.Modal(deleteModal);
        
        deleteButtons.forEach(button => {
            button.addEventListener('click', function() {
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
        });
    }

    // ===== Search and Filter Functionality =====
    const searchInput = document.getElementById('searchBouquet');
    const filterOccasion = document.getElementById('filterOccasion');
    const filterStatus = document.getElementById('filterStatus');
    const resetBtn = document.getElementById('resetFilters');
    const clearSearch = document.getElementById('clearSearch');
    const tableBody = document.getElementById('bouquetsTableBody');
    const rows = tableBody ? tableBody.getElementsByTagName('tr') : [];

    if (searchInput && filterOccasion && filterStatus) {
        
        function filterTable() {
            const searchTerm = searchInput.value.toLowerCase().trim();
            const occasionFilter = filterOccasion.value;
            const statusFilter = filterStatus.value;
            
            let visibleCount = 0;
            
            Array.from(rows).forEach(row => {
                // Skip empty state row
                if (row.querySelector('.empty-state')) return;
                
                const bouquetName = row.cells[2]?.querySelector('strong')?.textContent.toLowerCase() || '';
                const occasionTags = row.cells[6]?.textContent.toLowerCase() || '';
                const statusCell = row.cells[7]?.querySelector('.status-badge');
                const status = statusCell ? (statusCell.classList.contains('status-active') ? '1' : '0') : '';
                
                let matchesSearch = true;
                let matchesOccasion = true;
                let matchesStatus = true;
                
                // Search filter
                if (searchTerm) {
                    matchesSearch = bouquetName.includes(searchTerm) || occasionTags.includes(searchTerm);
                }
                
                // Occasion filter
                if (occasionFilter) {
                    matchesOccasion = occasionTags.includes(occasionFilter);
                }
                
                // Status filter
                if (statusFilter !== '') {
                    matchesStatus = status === statusFilter;
                }
                
                // Show/hide row
                if (matchesSearch && matchesOccasion && matchesStatus) {
                    row.style.display = '';
                    visibleCount++;
                } else {
                    row.style.display = 'none';
                }
            });
            
            // Show/hide clear search button
            if (searchTerm) {
                clearSearch.style.display = 'block';
            } else {
                clearSearch.style.display = 'none';
            }
        }
        
        // Event listeners
        searchInput.addEventListener('keyup', filterTable);
        filterOccasion.addEventListener('change', filterTable);
        filterStatus.addEventListener('change', filterTable);
        
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
                filterOccasion.value = '';
                filterStatus.value = '';
                clearSearch.style.display = 'none';
                filterTable();
            });
        }
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