/**
 * E-Menum Admin Change Form JavaScript
 *
 * Enhances Django admin change forms with:
 * - Auto-slug generation from title fields
 * - Image preview on file input change
 * - Confirmation dialogs for destructive actions
 * - JSON field formatting
 */

(function() {
    'use strict';

    document.addEventListener('DOMContentLoaded', function() {
        initAutoSlug();
        initImagePreview();
        initJsonFormatting();
        initDeleteConfirmation();
    });

    /**
     * Auto-generate slug from title/name fields.
     */
    function initAutoSlug() {
        var titleField = document.querySelector('#id_name, #id_title');
        var slugField = document.querySelector('#id_slug');

        if (!titleField || !slugField) return;
        if (slugField.value) return;  // Don't overwrite existing slugs

        titleField.addEventListener('input', function() {
            var slug = this.value
                .toLowerCase()
                .replace(/[^\w\s-]/g, '')
                .replace(/[\s_]+/g, '-')
                .replace(/^-+|-+$/g, '')
                .substring(0, 200);

            // Basic Turkish character replacement
            slug = slug
                .replace(/ş/g, 's').replace(/ç/g, 'c')
                .replace(/ğ/g, 'g').replace(/ü/g, 'u')
                .replace(/ö/g, 'o').replace(/ı/g, 'i');

            slugField.value = slug;
        });
    }

    /**
     * Show image preview when a file is selected.
     */
    function initImagePreview() {
        var fileInputs = document.querySelectorAll('input[type="file"]');
        fileInputs.forEach(function(input) {
            input.addEventListener('change', function(e) {
                var file = e.target.files[0];
                if (!file || !file.type.startsWith('image/')) return;

                var reader = new FileReader();
                reader.onload = function(ev) {
                    var existingPreview = input.parentNode.querySelector('.emenum-preview');
                    if (existingPreview) existingPreview.remove();

                    var img = document.createElement('img');
                    img.src = ev.target.result;
                    img.className = 'emenum-preview';
                    img.style.cssText = 'max-width:200px;max-height:150px;margin-top:8px;border-radius:6px;border:1px solid rgba(255,255,255,0.1);';
                    input.parentNode.appendChild(img);
                };
                reader.readAsDataURL(file);
            });
        });
    }

    /**
     * Pretty-format JSON fields.
     */
    function initJsonFormatting() {
        var textareas = document.querySelectorAll('textarea');
        textareas.forEach(function(textarea) {
            if (!textarea.value) return;
            try {
                var parsed = JSON.parse(textarea.value);
                textarea.value = JSON.stringify(parsed, null, 2);
                textarea.style.fontFamily = "'JetBrains Mono', 'Fira Code', monospace";
                textarea.style.fontSize = '0.8125rem';
                textarea.style.lineHeight = '1.5';
                textarea.rows = Math.min(Math.max(textarea.value.split('\n').length + 1, 4), 20);
            } catch(e) {
                // Not JSON, skip
            }
        });
    }

    /**
     * Add confirmation dialog to delete buttons.
     */
    function initDeleteConfirmation() {
        var deleteLinks = document.querySelectorAll('.deletelink, .inline-deletelink');
        deleteLinks.forEach(function(link) {
            link.addEventListener('click', function(e) {
                if (!confirm('Bu kaydi silmek istediginizden emin misiniz?')) {
                    e.preventDefault();
                }
            });
        });
    }

})();
