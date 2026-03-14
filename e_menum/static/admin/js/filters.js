/**
 * E-Menum Admin Filter Toolbar
 *
 * Transforms Django's hidden changelist-filter DOM into a modern
 * horizontal filter toolbar with:
 * - Dropdown buttons for each filter group
 * - Searchable dropdowns for large option lists (8+)
 * - Active filter chips with remove action
 * - "Clear all" button
 * - Enhanced search bar with clear button
 *
 * Architecture:
 *   Django renders {% admin_list_filter %} into a hidden
 *   #changelist-filter div. This script parses that DOM, extracts
 *   filter metadata, and builds an interactive toolbar in
 *   #filter-toolbar using vanilla JS.
 */

(function() {
    'use strict';

    document.addEventListener('DOMContentLoaded', function() {
        buildFilterToolbar();
        enhanceSearchBar();
    });


    /* ══════════════════════════════════════════════════════════
       MAIN: Build the horizontal filter toolbar
       ══════════════════════════════════════════════════════════ */
    function buildFilterToolbar() {
        var source = document.getElementById('changelist-filter');
        var toolbar = document.getElementById('filter-toolbar');
        if (!source || !toolbar) return;

        var filters = parseFilterSource(source);
        if (filters.length === 0) return;

        // Extract clear-all URL
        var clearAllUrl = '';
        var extraActions = source.querySelector('#changelist-filter-extra-actions a');
        if (extraActions) {
            clearAllUrl = extraActions.getAttribute('data-clear-url')
                       || extraActions.getAttribute('href')
                       || '';
        }

        // Check if any filter is actively set
        var hasActiveFilters = filters.some(function(f) { return f.hasActiveFilter; });

        // Build active filter chips
        if (hasActiveFilters) {
            var chipsRow = document.createElement('div');
            chipsRow.className = 'filter-chips';

            filters.forEach(function(filter) {
                if (!filter.hasActiveFilter) return;

                var chip = document.createElement('span');
                chip.className = 'filter-chip';
                chip.innerHTML =
                    '<span class="filter-chip-label">' + escapeHtml(filter.title) + ':</span> ' +
                    '<span class="filter-chip-value">' + escapeHtml(filter.selectedValue) + '</span>';

                // Find the "All" option to build a remove URL
                var allOption = null;
                for (var i = 0; i < filter.options.length; i++) {
                    if (filter.options[i].isAll) { allOption = filter.options[i]; break; }
                }
                if (allOption) {
                    var removeLink = document.createElement('a');
                    removeLink.href = allOption.href;
                    removeLink.className = 'filter-chip-remove';
                    removeLink.title = 'Remove filter';
                    removeLink.innerHTML = '<i class="ph ph-x"></i>';
                    chip.appendChild(removeLink);
                }

                chipsRow.appendChild(chip);
            });

            // Clear all button
            if (clearAllUrl) {
                var clearAll = document.createElement('a');
                clearAll.href = clearAllUrl;
                clearAll.className = 'filter-clear-all';
                clearAll.innerHTML = '<i class="ph ph-x"></i> Clear all';
                chipsRow.appendChild(clearAll);
            }

            toolbar.appendChild(chipsRow);
        }

        // Build filter dropdown buttons
        var dropdownsRow = document.createElement('div');
        dropdownsRow.className = 'filter-dropdowns';

        filters.forEach(function(filter, idx) {
            var dropdown = createFilterDropdown(filter, idx);
            dropdownsRow.appendChild(dropdown);
        });

        toolbar.appendChild(dropdownsRow);
    }


    /* ══════════════════════════════════════════════════════════
       PARSE: Extract filter data from hidden Django DOM
       ══════════════════════════════════════════════════════════ */
    function parseFilterSource(source) {
        var filters = [];

        // Django 5.x uses <details><summary>...<ul> pattern
        var detailsElements = source.querySelectorAll('details');
        if (detailsElements.length > 0) {
            for (var i = 0; i < detailsElements.length; i++) {
                var details = detailsElements[i];
                var summary = details.querySelector('summary');
                var ul = details.querySelector('ul');
                if (!summary || !ul) continue;
                filters.push(parseFilterGroup(summary.textContent.trim(), ul));
            }
            return filters;
        }

        // Fallback: Django 4.x uses <h3>...<ul> pairs
        var h3s = source.querySelectorAll('h3');
        for (var j = 0; j < h3s.length; j++) {
            var h3 = h3s[j];
            var nextUl = h3.nextElementSibling;
            while (nextUl && nextUl.tagName !== 'UL') {
                nextUl = nextUl.nextElementSibling;
            }
            if (!nextUl) continue;
            filters.push(parseFilterGroup(h3.textContent.trim(), nextUl));
        }

        return filters;
    }

    function parseFilterGroup(rawTitle, ul) {
        var options = [];
        var selectedValue = null;
        var currentPath = window.location.pathname;

        var lis = ul.querySelectorAll('li');
        for (var i = 0; i < lis.length; i++) {
            var li = lis[i];
            var a = li.querySelector('a');
            if (!a) continue;

            var isSelected = li.classList.contains('selected');
            var label = a.textContent.trim();
            var href = a.getAttribute('href') || '?';

            // Determine if this is the "All" / "Tumunu" option
            var isAll = (href === '?' || href === currentPath || href === currentPath + '?');

            options.push({
                label: label,
                href: href,
                selected: isSelected,
                isAll: isAll
            });

            if (isSelected && !isAll) {
                selectedValue = label;
            }
        }

        // Clean title: remove trailing indicators and common Django suffixes
        var title = rawTitle
            .replace(/\s*[\u25BC\u25B6\u25B2\u25C0]\s*$/g, '')  // arrows
            .replace(/^By\s+/i, '')                               // "By " prefix
            .replace(/\s+s\u00FCzgecine\s+g\u00F6re\s*$/i, '')   // Turkish "... suzgecine gore"
            .trim();

        return {
            title: title,
            options: options,
            selectedValue: selectedValue,
            hasActiveFilter: selectedValue !== null
        };
    }


    /* ══════════════════════════════════════════════════════════
       BUILD: Create a single filter dropdown component
       ══════════════════════════════════════════════════════════ */
    function createFilterDropdown(filter, index) {
        var wrapper = document.createElement('div');
        wrapper.className = 'filter-dropdown';

        var isOpen = false;
        var needsSearch = filter.options.length > 8;

        // --- Trigger button ---
        var btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'filter-dropdown-btn' + (filter.hasActiveFilter ? ' active' : '');

        var btnHTML = '<span class="filter-dropdown-label">' + escapeHtml(filter.title) + '</span>';
        if (filter.hasActiveFilter) {
            btnHTML += ' <span class="filter-dropdown-value">' + escapeHtml(truncate(filter.selectedValue, 18)) + '</span>';
        }
        btnHTML += ' <i class="ph ph-caret-down filter-dropdown-arrow"></i>';
        btn.innerHTML = btnHTML;

        // --- Dropdown panel ---
        var panel = document.createElement('div');
        panel.className = 'filter-dropdown-panel';
        panel.style.display = 'none';

        // Search input (for large lists)
        var searchInput = null;
        if (needsSearch) {
            searchInput = document.createElement('input');
            searchInput.type = 'text';
            searchInput.className = 'filter-dropdown-search';
            searchInput.placeholder = 'Ara...';
            searchInput.autocomplete = 'off';
            panel.appendChild(searchInput);
        }

        // Options container
        var optList = document.createElement('div');
        optList.className = 'filter-dropdown-options';

        for (var i = 0; i < filter.options.length; i++) {
            var opt = filter.options[i];
            var a = document.createElement('a');
            a.href = opt.href;
            a.className = 'filter-dropdown-option';
            if (opt.selected) a.classList.add('selected');
            if (opt.isAll && !opt.selected) a.classList.add('option-all');
            a.textContent = opt.label;
            optList.appendChild(a);
        }

        panel.appendChild(optList);

        // --- Event handlers ---

        // Toggle dropdown
        btn.addEventListener('click', function(e) {
            e.stopPropagation();

            if (isOpen) {
                isOpen = false;
                panel.style.display = 'none';
                btn.classList.remove('open');
            } else {
                // Close others first
                closeOtherDropdowns(wrapper);

                isOpen = true;
                panel.style.display = '';
                btn.classList.add('open');

                // Focus search if available
                if (searchInput) {
                    setTimeout(function() { searchInput.focus(); }, 50);
                }

                // Position adjustment if near right edge
                adjustPanelPosition(wrapper, panel);
            }
        });

        // Search within options
        if (searchInput) {
            searchInput.addEventListener('input', function() {
                var query = this.value.toLowerCase();
                var items = optList.querySelectorAll('.filter-dropdown-option');
                for (var k = 0; k < items.length; k++) {
                    var text = items[k].textContent.toLowerCase();
                    items[k].style.display = text.indexOf(query) !== -1 ? '' : 'none';
                }
            });

            searchInput.addEventListener('click', function(e) {
                e.stopPropagation();
            });
        }

        // Prevent panel clicks from closing (except link clicks)
        panel.addEventListener('click', function(e) {
            if (e.target.tagName === 'A') return;
            e.stopPropagation();
        });

        // Keyboard: Escape closes
        wrapper.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && isOpen) {
                isOpen = false;
                panel.style.display = 'none';
                btn.classList.remove('open');
                btn.focus();
            }
        });

        wrapper.appendChild(btn);
        wrapper.appendChild(panel);

        return wrapper;
    }


    /* ══════════════════════════════════════════════════════════
       HELPERS
       ══════════════════════════════════════════════════════════ */

    function closeOtherDropdowns(current) {
        var allDropdowns = document.querySelectorAll('.filter-dropdown');
        for (var i = 0; i < allDropdowns.length; i++) {
            if (allDropdowns[i] === current) continue;
            var p = allDropdowns[i].querySelector('.filter-dropdown-panel');
            var b = allDropdowns[i].querySelector('.filter-dropdown-btn');
            if (p) p.style.display = 'none';
            if (b) b.classList.remove('open');
        }
    }

    function adjustPanelPosition(wrapper, panel) {
        panel.style.left = '0';
        panel.style.right = 'auto';

        requestAnimationFrame(function() {
            var rect = panel.getBoundingClientRect();
            if (rect.right > window.innerWidth - 16) {
                panel.style.left = 'auto';
                panel.style.right = '0';
            }
        });
    }

    function escapeHtml(str) {
        if (!str) return '';
        var div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    function truncate(str, max) {
        if (!str) return '';
        return str.length > max ? str.substring(0, max) + '\u2026' : str;
    }

    // Global: close all dropdowns when clicking outside
    document.addEventListener('click', function() {
        var panels = document.querySelectorAll('.filter-dropdown-panel');
        var btns = document.querySelectorAll('.filter-dropdown-btn');
        for (var i = 0; i < panels.length; i++) {
            panels[i].style.display = 'none';
        }
        for (var j = 0; j < btns.length; j++) {
            btns[j].classList.remove('open');
        }
    });


    /* ══════════════════════════════════════════════════════════
       ENHANCED SEARCH BAR
       ══════════════════════════════════════════════════════════ */
    function enhanceSearchBar() {
        var searchForm = document.getElementById('changelist-search');
        if (!searchForm) return;

        var input = searchForm.querySelector('input[type="text"]');
        if (!input) return;

        // Add clear button if search has a value
        if (input.value && input.value.trim().length > 0) {
            var clearBtn = document.createElement('button');
            clearBtn.type = 'button';
            clearBtn.className = 'search-clear-btn';
            clearBtn.innerHTML = '<i class="ph ph-x-circle"></i>';
            clearBtn.title = 'Clear search';
            clearBtn.addEventListener('click', function() {
                input.value = '';
                input.closest('form').submit();
            });

            // Insert before the submit button
            var submitBtn = searchForm.querySelector('input[type="submit"]');
            if (submitBtn) {
                submitBtn.parentNode.insertBefore(clearBtn, submitBtn);
            } else {
                searchForm.appendChild(clearBtn);
            }
        }
    }

})();
