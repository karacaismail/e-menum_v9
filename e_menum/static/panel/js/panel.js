/**
 * E-Menum — Restaurant Owner Panel JS
 *
 * Shared Alpine.js stores and components for the panel:
 * - Toast notification system
 * - Global confirm dialog
 * - Form guard (unsaved changes detection)
 * - CSRF-aware fetch helper
 */

document.addEventListener('alpine:init', () => {

    // ── Global Toast System ──────────────────────────────────────────────
    Alpine.store('toasts', {
        items: [],
        counter: 0,

        /**
         * Add a toast notification.
         * @param {string} message
         * @param {'success'|'error'|'warning'|'info'} type
         * @param {number} duration  Auto-dismiss ms (0 = permanent)
         * @returns {number} Toast ID
         */
        add(message, type = 'info', duration = 5000) {
            const id = ++this.counter;
            this.items.push({ id, message, type, visible: true });
            if (duration > 0) {
                setTimeout(() => this.dismiss(id), duration);
            }
            return id;
        },

        dismiss(id) {
            const item = this.items.find(t => t.id === id);
            if (item) item.visible = false;
            setTimeout(() => {
                this.items = this.items.filter(t => t.id !== id);
            }, 300);
        },

        success(msg, duration)  { return this.add(msg, 'success', duration); },
        error(msg, duration)    { return this.add(msg, 'error', duration || 8000); },
        warning(msg, duration)  { return this.add(msg, 'warning', duration); },
        info(msg, duration)     { return this.add(msg, 'info', duration); },

        /**
         * Show a toast with an Undo button.
         * @param {string} message
         * @param {Function} undoCallback — called if user clicks "Geri Al"
         * @param {Function} [commitCallback] — called when undo window expires
         * @param {number} [duration=5000]
         */
        withUndo(message, undoCallback, commitCallback, duration = 5000) {
            const id = ++this.counter;
            this.items.push({ id, message, type: 'warning', visible: true, undoable: true });
            const timer = setTimeout(() => {
                this.dismiss(id);
                if (typeof commitCallback === 'function') commitCallback();
            }, duration);
            // Store undo handler
            this['_undo_' + id] = function() {
                clearTimeout(timer);
                if (typeof undoCallback === 'function') undoCallback();
            };
            return id;
        },

        undo(id) {
            const handler = this['_undo_' + id];
            if (handler) {
                handler();
                delete this['_undo_' + id];
            }
            this.dismiss(id);
        },
    });


    // ── Global Confirm Dialog ────────────────────────────────────────────
    Alpine.store('confirm', {
        open: false,
        title: '',
        message: '',
        confirmText: '',
        confirmClass: '',
        _resolve: null,

        /**
         * Show a confirm dialog and return a Promise<boolean>.
         * @param {object} opts
         * @param {string} opts.title
         * @param {string} opts.message
         * @param {string} [opts.confirmText='Onayla']
         * @param {boolean} [opts.danger=false]
         * @returns {Promise<boolean>}
         */
        show({ title, message, confirmText, danger = false }) {
            this.title = title;
            this.message = message;
            this.confirmText = confirmText || 'Onayla';
            this.confirmClass = danger
                ? 'bg-red-600 hover:bg-red-700 text-white'
                : 'bg-primary-600 hover:bg-primary-700 text-white';
            this.open = true;
            return new Promise(resolve => { this._resolve = resolve; });
        },

        accept() {
            this.open = false;
            if (this._resolve) this._resolve(true);
            this._resolve = null;
        },

        cancel() {
            this.open = false;
            if (this._resolve) this._resolve(false);
            this._resolve = null;
        },
    });


    // ── Form Guard (Unsaved Changes) ─────────────────────────────────────
    Alpine.data('formGuard', () => ({
        isDirty: false,
        _initialState: '',

        init() {
            const form = this.$el.querySelector('form');
            if (!form) return;

            // Snapshot initial form state
            this._initialState = new URLSearchParams(new FormData(form)).toString();

            form.addEventListener('input', () => {
                this.isDirty = new URLSearchParams(new FormData(form)).toString() !== this._initialState;
            });

            form.addEventListener('change', () => {
                this.isDirty = new URLSearchParams(new FormData(form)).toString() !== this._initialState;
            });

            form.addEventListener('submit', () => {
                this.isDirty = false;
            });

            window.addEventListener('beforeunload', (e) => {
                if (this.isDirty) {
                    e.preventDefault();
                    e.returnValue = '';
                }
            });
        }
    }));


    // ── Inline Validation ──────────────────────────────────────────────────
    Alpine.data('inlineValidation', () => ({
        errors: {},
        touched: {},

        rules: {
            required(value) {
                return (value && String(value).trim().length > 0) ? null : 'Bu alan zorunludur.';
            },
            minLength(min) {
                return function(value) {
                    if (!value) return null;
                    return String(value).trim().length >= min ? null : 'En az ' + min + ' karakter girilmelidir.';
                };
            },
            email(value) {
                if (!value) return null;
                return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value) ? null : 'Gecerli bir e-posta adresi giriniz.';
            },
            phone(value) {
                if (!value) return null;
                return /^[\d\s\-\+\(\)]{7,15}$/.test(value) ? null : 'Gecerli bir telefon numarasi giriniz.';
            },
            url(value) {
                if (!value) return null;
                try { new URL(value); return null; } catch { return 'Gecerli bir URL giriniz.'; }
            }
        },

        /**
         * Validate a single field.
         * @param {string} fieldName
         * @param {*} value
         * @param {string[]} ruleNames — e.g., ['required', 'email']
         */
        validate(fieldName, value, ruleNames) {
            this.touched[fieldName] = true;
            for (const ruleName of ruleNames) {
                let rule;
                if (typeof ruleName === 'function') {
                    rule = ruleName;
                } else if (ruleName.startsWith('minLength:')) {
                    rule = this.rules.minLength(parseInt(ruleName.split(':')[1]));
                } else {
                    rule = this.rules[ruleName];
                }
                if (rule) {
                    const error = rule(value);
                    if (error) {
                        this.errors[fieldName] = error;
                        return false;
                    }
                }
            }
            delete this.errors[fieldName];
            return true;
        },

        hasError(fieldName) {
            return this.touched[fieldName] && !!this.errors[fieldName];
        },

        getError(fieldName) {
            return this.errors[fieldName] || '';
        },

        isValid(fieldName) {
            return this.touched[fieldName] && !this.errors[fieldName];
        },

        get formValid() {
            return Object.keys(this.errors).length === 0;
        }
    }));


    // ── Submit Button Loading State ────────────────────────────────────────
    Alpine.data('submitLoading', () => ({
        submitting: false,

        init() {
            const form = this.$el.closest('form') || this.$el.querySelector('form');
            if (form) {
                form.addEventListener('submit', () => {
                    this.submitting = true;
                });
            }
        }
    }));
});


// ── Debounce Utility ─────────────────────────────────────────────────────
window.debounce = function(fn, delay) {
    var timer = null;
    return function() {
        var context = this;
        var args = arguments;
        clearTimeout(timer);
        timer = setTimeout(function() {
            fn.apply(context, args);
        }, delay);
    };
};


// ── CSRF-aware Fetch Helper ──────────────────────────────────────────────
window.fetchWithCsrf = function(url, options) {
    options = options || {};

    var csrfToken = '';
    var csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
    if (csrfInput) {
        csrfToken = csrfInput.value;
    } else {
        var cookie = document.cookie.split(';').find(function(c) {
            return c.trim().startsWith('csrftoken=');
        });
        csrfToken = cookie ? cookie.split('=')[1] : '';
    }

    options.headers = Object.assign({
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken,
        'X-Requested-With': 'XMLHttpRequest'
    }, options.headers || {});

    return fetch(url, options);
};


// ── Backward Compat: override old showToast ──────────────────────────────
window.showToast = function(message, type, duration) {
    if (window.Alpine && Alpine.store('toasts')) {
        Alpine.store('toasts').add(message, type || 'info', duration);
    }
};


// ── Keyboard Shortcuts ───────────────────────────────────────────────────
(function() {
    var shortcutsModalId = 'panel-shortcuts-modal';

    document.addEventListener('keydown', function(e) {
        // Don't trigger shortcuts when typing in inputs
        var tag = (e.target.tagName || '').toLowerCase();
        if (tag === 'input' || tag === 'textarea' || tag === 'select' || e.target.isContentEditable) {
            // But still allow Escape
            if (e.key !== 'Escape') return;
        }

        var isMod = e.metaKey || e.ctrlKey;

        // Ctrl/Cmd + K — Focus search input
        if (isMod && e.key === 'k') {
            e.preventDefault();
            var searchInput = document.querySelector('input[type="search"], input[name="q"], input[placeholder*="Ara"]');
            if (searchInput) {
                searchInput.focus();
                searchInput.select();
            }
            return;
        }

        // Ctrl/Cmd + S — Submit active form
        if (isMod && e.key === 's') {
            e.preventDefault();
            var form = document.querySelector('form:not(#changelist-form)');
            if (form) {
                var submitBtn = form.querySelector('[type="submit"]');
                if (submitBtn) submitBtn.click();
            }
            return;
        }

        // ? or Ctrl/Cmd + / — Show shortcuts modal
        if ((e.key === '?' && !isMod) || (isMod && e.key === '/')) {
            e.preventDefault();
            var modal = document.getElementById(shortcutsModalId);
            if (modal) {
                var isOpen = modal.style.display !== 'none';
                modal.style.display = isOpen ? 'none' : 'flex';
            }
            return;
        }

        // Escape — Close modals/dialogs
        if (e.key === 'Escape') {
            var modal = document.getElementById(shortcutsModalId);
            if (modal) modal.style.display = 'none';
            return;
        }
    });
})();


// ── Filter Persistence (sessionStorage) ──────────────────────────────────
(function() {
    var FILTER_KEY = 'panel_filters_' + window.location.pathname;

    // On page load, restore filter values from sessionStorage
    document.addEventListener('DOMContentLoaded', function() {
        try {
            var saved = sessionStorage.getItem(FILTER_KEY);
            if (!saved) return;
            var filters = JSON.parse(saved);
            Object.keys(filters).forEach(function(name) {
                var input = document.querySelector('[name="' + name + '"]');
                if (input && !input.value) {
                    input.value = filters[name];
                }
            });
        } catch (e) { /* ignore parse errors */ }
    });

    // Before navigating away, save current filter values
    window.addEventListener('beforeunload', function() {
        try {
            var filterInputs = document.querySelectorAll(
                'form select[name], form input[name][type="search"], form input[name][type="text"]'
            );
            var filters = {};
            filterInputs.forEach(function(input) {
                if (input.value && input.name !== 'csrfmiddlewaretoken') {
                    filters[input.name] = input.value;
                }
            });
            if (Object.keys(filters).length > 0) {
                sessionStorage.setItem(FILTER_KEY, JSON.stringify(filters));
            } else {
                sessionStorage.removeItem(FILTER_KEY);
            }
        } catch (e) { /* ignore */ }
    });

    // Clear filters helper
    window.clearPanelFilters = function() {
        sessionStorage.removeItem(FILTER_KEY);
    };
})();
