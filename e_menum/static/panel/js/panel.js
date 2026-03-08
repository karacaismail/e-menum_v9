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
});


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
