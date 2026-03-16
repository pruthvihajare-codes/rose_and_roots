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
    const filterCategory = document.getElementById('filterCategory');  // Added category filter
    const filterStatus = document.getElementById('filterStatus');
    const resetBtn = document.getElementById('resetFilters');
    const clearSearch = document.getElementById('clearSearch');
    const tableBody = document.getElementById('bouquetsTableBody');
    const rows = tableBody ? tableBody.getElementsByTagName('tr') : [];

    // Add data attributes to rows for better filtering
    if (rows.length > 0) {
        Array.from(rows).forEach(row => {
            // Skip empty state row
            if (row.querySelector('.empty-state')) return;
            
            // Add category data attribute
            const categoryCell = row.cells[3]?.querySelector('.category-badge');
            if (categoryCell) {
                const categoryText = categoryCell.textContent.trim();
                // Find matching category in filter dropdown
                if (filterCategory) {
                    const categoryOptions = Array.from(filterCategory.options);
                    const matchingOption = categoryOptions.find(opt => 
                        opt.text.trim() === categoryText
                    );
                    if (matchingOption) {
                        row.dataset.categoryId = matchingOption.value;
                    } else {
                        row.dataset.categoryId = 'uncategorized';
                    }
                }
            }
            
            // Add occasion data for better filtering
            const occasionCell = row.cells[7]?.querySelector('.occasion-tags');
            if (occasionCell) {
                row.dataset.occasionText = occasionCell.textContent.toLowerCase();
            }
        });
    }

    if (searchInput && filterOccasion && filterCategory && filterStatus) {
        
        function filterTable() {
            const searchTerm = searchInput.value.toLowerCase().trim();
            const occasionFilter = filterOccasion.value;
            const categoryFilter = filterCategory.value;  // Get category filter value
            const statusFilter = filterStatus.value;
            
            let visibleCount = 0;
            
            Array.from(rows).forEach(row => {
                // Skip empty state row
                if (row.querySelector('.empty-state')) return;
                
                const bouquetName = row.cells[2]?.querySelector('strong')?.textContent.toLowerCase() || '';
                const occasionTags = row.cells[7]?.textContent.toLowerCase() || '';
                const rowCategoryId = row.dataset.categoryId || '';  // Get row's category ID
                const statusCell = row.cells[8]?.querySelector('.status-badge');  // Updated index for status
                const status = statusCell ? (statusCell.classList.contains('status-active') ? '1' : '0') : '';
                
                let matchesSearch = true;
                let matchesOccasion = true;
                let matchesCategory = true;  // New category match flag
                let matchesStatus = true;
                
                // Search filter
                if (searchTerm) {
                    matchesSearch = bouquetName.includes(searchTerm) || occasionTags.includes(searchTerm);
                }
                
                // Occasion filter
                if (occasionFilter) {
                    // Get the selected occasion text
                    const selectedOption = filterOccasion.options[filterOccasion.selectedIndex];
                    const selectedOccasionText = selectedOption.text.toLowerCase();
                    matchesOccasion = occasionTags.includes(selectedOccasionText);
                }
                
                // Category filter - NEW
                if (categoryFilter) {
                    matchesCategory = rowCategoryId === categoryFilter;
                }
                
                // Status filter
                if (statusFilter !== '') {
                    matchesStatus = status === statusFilter;
                }
                
                // Show/hide row - include category match
                if (matchesSearch && matchesOccasion && matchesCategory && matchesStatus) {
                    row.style.display = '';
                    visibleCount++;
                } else {
                    row.style.display = 'none';
                }
            });
            
            // Show/hide clear search button
            if (clearSearch) {
                clearSearch.style.display = searchTerm ? 'block' : 'none';
            }
            
            // Show empty state if no results
            showEmptyState(visibleCount === 0);
        }
        
        // Function to show empty state when no results
        function showEmptyState(show) {
            let emptyRow = document.querySelector('.empty-state-row');
            
            if (show) {
                if (!emptyRow && rows.length > 0) {
                    const firstRow = rows[0];
                    const emptyRowHtml = `
                        <tr class="empty-state-row">
                            <td colspan="10" class="text-center py-5">
                                <div class="empty-state">
                                    <i class="bi bi-flower2 empty-icon"></i>
                                    <h5>No Bouquets Found</h5>
                                    <p>No bouquets match your filter criteria. Try adjusting your filters.</p>
                                    <button class="btn btn-add-bouquet mt-3" id="clearAllFilters">
                                        <i class="bi bi-arrow-counterclockwise me-2"></i>Clear All Filters
                                    </button>
                                </div>
                            </td>
                        </tr>
                    `;
                    firstRow.insertAdjacentHTML('beforebegin', emptyRowHtml);
                    
                    // Add event listener to the clear filters button
                    document.getElementById('clearAllFilters')?.addEventListener('click', function() {
                        resetFilters();
                    });
                }
            } else {
                if (emptyRow) {
                    emptyRow.remove();
                }
            }
        }
        
        // Event listeners
        searchInput.addEventListener('input', filterTable);
        filterOccasion.addEventListener('change', filterTable);
        filterCategory.addEventListener('change', filterTable);  // Added category filter listener
        filterStatus.addEventListener('change', filterTable);
        
        // Clear search
        if (clearSearch) {
            clearSearch.addEventListener('click', function() {
                searchInput.value = '';
                filterTable();
            });
        }
        
        // Reset filters function
        function resetFilters() {
            searchInput.value = '';
            filterOccasion.value = '';
            filterCategory.value = '';  // Reset category filter
            filterStatus.value = '';
            if (clearSearch) {
                clearSearch.style.display = 'none';
            }
            filterTable();
        }
        
        // Reset filters
        if (resetBtn) {
            resetBtn.addEventListener('click', resetFilters);
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