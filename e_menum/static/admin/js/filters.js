/**
 * E-Menum Admin Filter Enhancement JavaScript
 *
 * Enhances Django admin changelist filters with:
 * - Collapsible filter sections
 * - Quick search within filter options
 * - Active filter count badge
 * - Clear all filters button
 */

(function() {
    'use strict';

    document.addEventListener('DOMContentLoaded', function() {
        initCollapsibleFilters();
        initFilterSearch();
        initActiveFilterBadge();
        initClearAllFilters();
    });

    /**
     * Make filter sections collapsible.
     */
    function initCollapsibleFilters() {
        var filterLists = document.querySelectorAll('#changelist-filter h3');
        filterLists.forEach(function(h3) {
            h3.style.cursor = 'pointer';
            h3.style.userSelect = 'none';
            h3.style.display = 'flex';
            h3.style.justifyContent = 'space-between';
            h3.style.alignItems = 'center';

            // Add collapse indicator
            var indicator = document.createElement('span');
            indicator.textContent = '\u25BC';  // Down arrow
            indicator.style.fontSize = '0.625rem';
            indicator.style.transition = 'transform 200ms ease';
            h3.appendChild(indicator);

            h3.addEventListener('click', function() {
                var ul = this.nextElementSibling;
                if (!ul || ul.tagName !== 'UL') return;

                var isHidden = ul.style.display === 'none';
                ul.style.display = isHidden ? '' : 'none';
                indicator.style.transform = isHidden ? '' : 'rotate(-90deg)';
            });
        });
    }

    /**
     * Add search input to filter sidebar if many options exist.
     */
    function initFilterSearch() {
        var filterDiv = document.querySelector('#changelist-filter');
        if (!filterDiv) return;

        var lists = filterDiv.querySelectorAll('ul');
        lists.forEach(function(ul) {
            if (ul.children.length < 8) return;

            var search = document.createElement('input');
            search.type = 'text';
            search.placeholder = 'Filtrele...';
            search.style.cssText = 'width:100%;padding:4px 8px;margin-bottom:6px;font-size:0.75rem;border:1px solid var(--emenum-border, #d1d5db);border-radius:4px;';

            search.addEventListener('input', function() {
                var query = this.value.toLowerCase();
                var items = ul.querySelectorAll('li');
                items.forEach(function(li) {
                    var text = li.textContent.toLowerCase();
                    li.style.display = text.indexOf(query) !== -1 ? '' : 'none';
                });
            });

            ul.parentNode.insertBefore(search, ul);
        });
    }

    /**
     * Show count of active filters as badge.
     */
    function initActiveFilterBadge() {
        var filterDiv = document.querySelector('#changelist-filter');
        if (!filterDiv) return;

        var h2 = filterDiv.querySelector('h2');
        if (!h2) return;

        var activeCount = filterDiv.querySelectorAll('li.selected').length;
        // Subtract "All" selections
        var allSelected = filterDiv.querySelectorAll('li.selected a[href="?"]').length;
        activeCount = Math.max(0, activeCount - allSelected);

        if (activeCount > 0) {
            var badge = document.createElement('span');
            badge.textContent = activeCount;
            badge.style.cssText = 'background:#6366f1;color:white;font-size:0.625rem;padding:2px 6px;border-radius:9999px;margin-left:6px;font-weight:700;';
            h2.appendChild(badge);
        }
    }

    /**
     * Add "Clear all filters" button.
     */
    function initClearAllFilters() {
        var filterDiv = document.querySelector('#changelist-filter');
        if (!filterDiv) return;

        var h2 = filterDiv.querySelector('h2');
        if (!h2) return;

        // Check if any filter is active
        var hasActiveFilter = window.location.search.length > 1;
        if (!hasActiveFilter) return;

        var clearBtn = document.createElement('a');
        clearBtn.href = window.location.pathname;
        clearBtn.textContent = 'Tumunu temizle';
        clearBtn.style.cssText = 'display:block;text-align:center;padding:6px 12px;margin-top:12px;font-size:0.75rem;color:#ef4444;border:1px solid rgba(239,68,68,0.2);border-radius:6px;text-decoration:none;';
        clearBtn.addEventListener('mouseenter', function() {
            this.style.background = 'rgba(239,68,68,0.08)';
        });
        clearBtn.addEventListener('mouseleave', function() {
            this.style.background = '';
        });

        filterDiv.appendChild(clearBtn);
    }

})();
