/**
 * E-Menum Admin UX Enhancement Module
 *
 * Enterprise-grade admin UX features:
 * 1. Toast notification system (Alpine store)
 * 2. Command palette / global search (Ctrl+K / Cmd+K)
 * 3. Keyboard shortcuts manager
 * 4. Form guard (unsaved changes detection)
 * 5. Page transition animations
 * 6. Floating save bar for forms
 */

(function () {
  'use strict';

  /* ═══════════════════════════════════════════════════════════
     1. TOAST NOTIFICATION SYSTEM
     ═══════════════════════════════════════════════════════════ */

  document.addEventListener('alpine:init', function () {
    Alpine.store('toasts', {
      items: [],
      _counter: 0,

      /**
       * Show a toast notification.
       * @param {string} message - The message to display
       * @param {string} type - 'success' | 'error' | 'warning' | 'info'
       * @param {number} duration - Auto-dismiss duration in ms (0 = persistent)
       */
      show: function (message, type, duration) {
        type = type || 'info';
        duration = duration !== undefined ? duration : 4000;
        var id = ++this._counter;
        var toast = { id: id, message: message, type: type, visible: true };
        this.items.push(toast);

        if (duration > 0) {
          var self = this;
          setTimeout(function () {
            self.dismiss(id);
          }, duration);
        }

        // Keep stack manageable
        if (this.items.length > 6) {
          this.items.shift();
        }

        return id;
      },

      success: function (msg, dur) { return this.show(msg, 'success', dur); },
      error: function (msg, dur) { return this.show(msg, 'error', dur || 6000); },
      warning: function (msg, dur) { return this.show(msg, 'warning', dur || 5000); },
      info: function (msg, dur) { return this.show(msg, 'info', dur); },

      dismiss: function (id) {
        var idx = this.items.findIndex(function (t) { return t.id === id; });
        if (idx !== -1) {
          this.items[idx].visible = false;
          var self = this;
          setTimeout(function () {
            self.items = self.items.filter(function (t) { return t.id !== id; });
          }, 300);
        }
      },

      clear: function () { this.items = []; }
    });

    // Backward compat
    window.showToast = function (msg, type, dur) {
      return Alpine.store('toasts').show(msg, type, dur);
    };

    /* ═══════════════════════════════════════════════════════════
       2. COMMAND PALETTE (Ctrl+K / Cmd+K)
       ═══════════════════════════════════════════════════════════ */

    Alpine.store('cmdPalette', {
      open: false,
      query: '',
      results: [],
      selectedIndex: 0,
      loading: false,
      recentPages: [],

      _allItems: null,

      init: function () {
        // Load recent pages from localStorage
        try {
          this.recentPages = JSON.parse(localStorage.getItem('emenum_recent_pages') || '[]');
        } catch (e) {
          this.recentPages = [];
        }
      },

      toggle: function () {
        this.open = !this.open;
        if (this.open) {
          this.query = '';
          this.selectedIndex = 0;
          this.results = this._getRecentOrDefault();
        }
      },

      close: function () {
        this.open = false;
        this.query = '';
        this.results = [];
      },

      search: function (query) {
        this.query = query;
        this.selectedIndex = 0;

        if (!query || query.length < 2) {
          this.results = this._getRecentOrDefault();
          return;
        }

        // Search via API
        var self = this;
        this.loading = true;

        fetch('/admin/api/search/?q=' + encodeURIComponent(query))
          .then(function (r) { return r.json(); })
          .then(function (data) {
            self.loading = false;
            if (data.results && data.results.length > 0) {
              self.results = data.results.map(function (r) {
                return {
                  label: r.title || r.label || r.name,
                  url: r.url,
                  icon: r.icon || 'file',
                  category: r.category || r.type || '',
                  description: r.description || r.subtitle || ''
                };
              });
            } else {
              self.results = self._getStaticResults(query);
            }
          })
          .catch(function () {
            self.loading = false;
            self.results = self._getStaticResults(query);
          });
      },

      selectNext: function () {
        if (this.selectedIndex < this.results.length - 1) this.selectedIndex++;
      },

      selectPrev: function () {
        if (this.selectedIndex > 0) this.selectedIndex--;
      },

      go: function (index) {
        var item = this.results[index !== undefined ? index : this.selectedIndex];
        if (item && item.url) {
          this._addRecent(item);
          window.location.href = item.url;
        }
      },

      _addRecent: function (item) {
        this.recentPages = this.recentPages.filter(function (r) { return r.url !== item.url; });
        this.recentPages.unshift({ label: item.label, url: item.url, icon: item.icon });
        if (this.recentPages.length > 8) this.recentPages = this.recentPages.slice(0, 8);
        try {
          localStorage.setItem('emenum_recent_pages', JSON.stringify(this.recentPages));
        } catch (e) { /* quota */ }
      },

      _getRecentOrDefault: function () {
        if (this.recentPages.length > 0) {
          return this.recentPages.map(function (r) {
            return { label: r.label, url: r.url, icon: r.icon || 'clock', category: 'Recent' };
          });
        }
        return this._getDefaultItems();
      },

      _getDefaultItems: function () {
        return [
          { label: 'Dashboard', url: '/admin/', icon: 'squares-four', category: 'Navigation' },
          { label: 'Organizations', url: '/admin/core/organization/', icon: 'buildings', category: 'Core' },
          { label: 'Users', url: '/admin/core/user/', icon: 'users', category: 'Core' },
          { label: 'Menus', url: '/admin/menu/menu/', icon: 'book-open', category: 'Menu' },
          { label: 'Products', url: '/admin/menu/product/', icon: 'package', category: 'Menu' },
          { label: 'Orders', url: '/admin/orders/order/', icon: 'receipt', category: 'Orders' },
          { label: 'Plans', url: '/admin/subscriptions/plan/', icon: 'credit-card', category: 'Subscriptions' },
          { label: 'Settings', url: '/admin/settings/', icon: 'gear', category: 'System' }
        ];
      },

      _getStaticResults: function (q) {
        var lower = q.toLowerCase();
        var all = this._getAllNavItems();
        return all.filter(function (item) {
          return item.label.toLowerCase().indexOf(lower) !== -1 ||
                 (item.category && item.category.toLowerCase().indexOf(lower) !== -1);
        }).slice(0, 12);
      },

      _getAllNavItems: function () {
        if (this._allItems) return this._allItems;
        this._allItems = [
          // Dashboard
          { label: 'Dashboard', url: '/admin/', icon: 'squares-four', category: 'Panel' },
          { label: 'Mainboard', url: '/admin/dashboard/', icon: 'chart-line-up', category: 'Panel' },
          // Core
          { label: 'Organizations', url: '/admin/core/organization/', icon: 'buildings', category: 'Core' },
          { label: 'Branches', url: '/admin/core/branch/', icon: 'map-pin', category: 'Core' },
          { label: 'Users', url: '/admin/core/user/', icon: 'users', category: 'Core' },
          { label: 'Roles', url: '/admin/core/role/', icon: 'shield', category: 'Core' },
          { label: 'Permissions', url: '/admin/core/permission/', icon: 'lock-key', category: 'Core' },
          { label: 'Permission Matrix', url: '/admin/permission-matrix/', icon: 'grid-four', category: 'Core' },
          { label: 'Audit Logs', url: '/admin/core/auditlog/', icon: 'clipboard-text', category: 'Core' },
          // Menu
          { label: 'Menus', url: '/admin/menu/menu/', icon: 'book-open', category: 'Menu' },
          { label: 'Categories', url: '/admin/menu/category/', icon: 'folders', category: 'Menu' },
          { label: 'Products', url: '/admin/menu/product/', icon: 'package', category: 'Menu' },
          { label: 'Themes', url: '/admin/menu/theme/', icon: 'palette', category: 'Menu' },
          { label: 'Allergens', url: '/admin/menu/allergen/', icon: 'warning', category: 'Menu' },
          // Orders
          { label: 'Orders', url: '/admin/orders/order/', icon: 'receipt', category: 'Orders' },
          { label: 'Tables', url: '/admin/orders/table/', icon: 'armchair', category: 'Orders' },
          { label: 'Zones', url: '/admin/orders/zone/', icon: 'map-trifold', category: 'Orders' },
          { label: 'QR Codes', url: '/admin/orders/qrcode/', icon: 'qr-code', category: 'Orders' },
          { label: 'Service Requests', url: '/admin/orders/servicerequest/', icon: 'bell-ringing', category: 'Orders' },
          // Subscriptions
          { label: 'Plans', url: '/admin/subscriptions/plan/', icon: 'credit-card', category: 'Subscriptions' },
          { label: 'Features', url: '/admin/subscriptions/feature/', icon: 'puzzle-piece', category: 'Subscriptions' },
          { label: 'Subscriptions', url: '/admin/subscriptions/subscription/', icon: 'repeat', category: 'Subscriptions' },
          { label: 'Invoices', url: '/admin/subscriptions/invoice/', icon: 'receipt', category: 'Subscriptions' },
          // Customers
          { label: 'Customers', url: '/admin/customers/customer/', icon: 'user', category: 'Customers' },
          { label: 'Feedback', url: '/admin/customers/feedback/', icon: 'chat-dots', category: 'Customers' },
          // Media
          { label: 'Media Library', url: '/admin/media-library/', icon: 'images', category: 'Media' },
          { label: 'Media Files', url: '/admin/media/media/', icon: 'image', category: 'Media' },
          { label: 'Media Folders', url: '/admin/media/mediafolder/', icon: 'folder', category: 'Media' },
          // CMS
          { label: 'Blog Posts', url: '/admin/website/blogpost/', icon: 'article', category: 'CMS' },
          { label: 'FAQ', url: '/admin/website/faq/', icon: 'question', category: 'CMS' },
          { label: 'Legal Pages', url: '/admin/website/legalpage/', icon: 'file-text', category: 'CMS' },
          { label: 'Site Settings', url: '/admin/website/sitesettings/', icon: 'gear', category: 'CMS' },
          { label: 'Navigation Links', url: '/admin/website/navigationlink/', icon: 'list', category: 'CMS' },
          { label: 'Testimonials', url: '/admin/website/testimonial/', icon: 'quotes', category: 'CMS' },
          // SEO
          { label: 'Redirects', url: '/admin/seo/redirect/', icon: 'arrows-split', category: 'SEO' },
          { label: '404 Logs', url: '/admin/seo/notfound404log/', icon: 'warning', category: 'SEO' },
          { label: 'SEO Dashboard', url: '/admin/seo-dashboard/', icon: 'chart-bar', category: 'SEO' },
          { label: 'Shield Dashboard', url: '/admin/shield-dashboard/', icon: 'shield', category: 'SEO' },
          // AI
          { label: 'AI Providers', url: '/admin/ai/aiproviderconfig/', icon: 'gear-six', category: 'AI' },
          { label: 'AI Generation History', url: '/admin/ai/aigeneration/', icon: 'sparkle', category: 'AI' },
          // Settings & Tools
          { label: 'Settings', url: '/admin/settings/', icon: 'gear', category: 'System' },
          { label: 'Reports', url: '/admin/reports/', icon: 'chart-bar', category: 'System' },
        ];
        return this._allItems;
      }
    });

    /* ═══════════════════════════════════════════════════════════
       3. CONFIRM DIALOG (Promise-based)
       ═══════════════════════════════════════════════════════════ */

    Alpine.store('confirm', {
      open: false,
      title: '',
      message: '',
      confirmLabel: 'Confirm',
      cancelLabel: 'Cancel',
      variant: 'danger',
      _resolve: null,

      show: function (opts) {
        opts = opts || {};
        this.title = opts.title || 'Are you sure?';
        this.message = opts.message || '';
        this.confirmLabel = opts.confirmLabel || 'Confirm';
        this.cancelLabel = opts.cancelLabel || 'Cancel';
        this.variant = opts.variant || 'danger';
        this.open = true;

        var self = this;
        return new Promise(function (resolve) {
          self._resolve = resolve;
        });
      },

      accept: function () {
        this.open = false;
        if (this._resolve) this._resolve(true);
        this._resolve = null;
      },

      cancel: function () {
        this.open = false;
        if (this._resolve) this._resolve(false);
        this._resolve = null;
      }
    });

    /* ═══════════════════════════════════════════════════════════
       4. FORM GUARD (unsaved changes detection)
       ═══════════════════════════════════════════════════════════ */

    Alpine.data('formGuard', function () {
      return {
        isDirty: false,
        isSaving: false,
        _initialData: null,

        init: function () {
          var self = this;
          var form = this.$el;

          // Capture initial state after slight delay (let widgets initialize)
          setTimeout(function () {
            self._initialData = new FormData(form);
            self._initialSnapshot = self._serialize(self._initialData);
          }, 500);

          // Listen for changes
          form.addEventListener('input', function () { self._checkDirty(); });
          form.addEventListener('change', function () { self._checkDirty(); });

          // Intercept form submit
          form.addEventListener('submit', function () {
            self.isSaving = true;
            self.isDirty = false;
          });

          // beforeunload warning
          window.addEventListener('beforeunload', function (e) {
            if (self.isDirty && !self.isSaving) {
              e.preventDefault();
              e.returnValue = '';
            }
          });
        },

        _checkDirty: function () {
          if (!this._initialSnapshot) return;
          var current = this._serialize(new FormData(this.$el));
          this.isDirty = current !== this._initialSnapshot;
        },

        _serialize: function (fd) {
          var parts = [];
          fd.forEach(function (val, key) {
            // Skip CSRF and management form fields
            if (key === 'csrfmiddlewaretoken') return;
            if (key.indexOf('__prefix__') !== -1) return;
            parts.push(key + '=' + val);
          });
          return parts.sort().join('&');
        }
      };
    });
  });


  /* ═══════════════════════════════════════════════════════════
     5. KEYBOARD SHORTCUTS
     ═══════════════════════════════════════════════════════════ */

  document.addEventListener('keydown', function (e) {
    // Don't trigger in inputs/textareas/selects
    var tag = document.activeElement ? document.activeElement.tagName : '';
    var inInput = tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT';
    var isEditable = document.activeElement && document.activeElement.isContentEditable;

    // Cmd/Ctrl + K → Command palette
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
      e.preventDefault();
      if (typeof Alpine !== 'undefined') {
        Alpine.store('cmdPalette').toggle();
      }
      return;
    }

    // Escape → Close command palette
    if (e.key === 'Escape') {
      if (typeof Alpine !== 'undefined') {
        var cp = Alpine.store('cmdPalette');
        if (cp.open) {
          cp.close();
          e.preventDefault();
          return;
        }
        var cf = Alpine.store('confirm');
        if (cf.open) {
          cf.cancel();
          e.preventDefault();
          return;
        }
      }
    }

    // Skip remaining shortcuts if in input
    if (inInput || isEditable) return;

    // ? → Keyboard shortcuts help
    if (e.key === '?' && !e.ctrlKey && !e.metaKey) {
      var helpModal = document.getElementById('keyboard-shortcuts-modal');
      if (helpModal) {
        var isVisible = helpModal.style.display !== 'none';
        helpModal.style.display = isVisible ? 'none' : 'flex';
        e.preventDefault();
      }
    }

    // g then d → Go to dashboard
    // g then u → Go to users
    // g then o → Go to organizations
    // g then m → Go to menus
    // g then s → Go to settings
    if (e.key === 'g' && !e.ctrlKey && !e.metaKey) {
      window._pendingGo = true;
      setTimeout(function () { window._pendingGo = false; }, 1000);
      return;
    }

    if (window._pendingGo) {
      window._pendingGo = false;
      var goMap = {
        'd': '/admin/',
        'u': '/admin/core/user/',
        'o': '/admin/core/organization/',
        'm': '/admin/menu/menu/',
        's': '/admin/settings/',
        'p': '/admin/menu/product/',
        'r': '/admin/reports/',
        'i': '/admin/subscriptions/invoice/'
      };
      if (goMap[e.key]) {
        e.preventDefault();
        window.location.href = goMap[e.key];
      }
    }
  });


  /* ═══════════════════════════════════════════════════════════
     6. PAGE TRANSITIONS & POLISH
     ═══════════════════════════════════════════════════════════ */

  // Smooth content entrance animation
  document.addEventListener('DOMContentLoaded', function () {
    var content = document.getElementById('content');
    if (content) {
      content.classList.add('ux-content-enter');
    }

    // Auto-dismiss Django messages after 5 seconds
    var messages = document.querySelectorAll('.message-list .message');
    if (messages.length > 0) {
      setTimeout(function () {
        messages.forEach(function (msg) {
          msg.style.transition = 'opacity 0.3s, transform 0.3s';
          msg.style.opacity = '0';
          msg.style.transform = 'translateY(-8px)';
          setTimeout(function () {
            if (msg.parentNode) msg.parentNode.removeChild(msg);
          }, 300);
        });
      }, 5000);
    }

    // Convert Django messages to toasts (deferred to let Alpine init)
    setTimeout(function () {
      if (typeof Alpine !== 'undefined' && Alpine.store('toasts')) {
        messages.forEach(function (msg) {
          var text = msg.querySelector('span');
          if (!text) return;
          var type = 'info';
          if (msg.classList.contains('message--success')) type = 'success';
          else if (msg.classList.contains('message--error')) type = 'error';
          else if (msg.classList.contains('message--warning')) type = 'warning';
          Alpine.store('toasts').show(text.textContent.trim(), type);
        });
      }
    }, 600);

    // Track current page for recent pages
    setTimeout(function () {
      if (typeof Alpine !== 'undefined' && Alpine.store('cmdPalette')) {
        var title = document.title.split('|')[0].trim();
        var url = window.location.pathname;
        if (url !== '/admin/' && url.startsWith('/admin/')) {
          var cp = Alpine.store('cmdPalette');
          cp._addRecent({ label: title, url: url, icon: 'file' });
        }
      }
    }, 1000);
  });


  /* ═══════════════════════════════════════════════════════════
     7. CHANGELIST ENHANCEMENTS
     ═══════════════════════════════════════════════════════════ */

  document.addEventListener('DOMContentLoaded', function () {
    // Sticky table headers
    var resultTable = document.querySelector('#result_list');
    if (resultTable) {
      var thead = resultTable.querySelector('thead');
      if (thead) {
        thead.classList.add('ux-sticky-header');
      }
    }

    // Add result count badge to page title
    var paginator = document.querySelector('.paginator');
    var pageTitle = document.querySelector('.page-title');
    if (paginator && pageTitle) {
      var countText = paginator.textContent.match(/(\d+)\s*(result|sonuç|kayıt)/i);
      if (countText) {
        var badge = document.createElement('span');
        badge.className = 'ux-result-count';
        badge.textContent = countText[1];
        pageTitle.appendChild(badge);
      }
    }

    // Keyboard navigation in result list
    var rows = document.querySelectorAll('#result_list tbody tr');
    if (rows.length > 0) {
      rows.forEach(function (row) {
        // Make rows keyboard-focusable
        row.setAttribute('tabindex', '0');
        row.addEventListener('keydown', function (e) {
          if (e.key === 'Enter') {
            var link = row.querySelector('a');
            if (link) link.click();
          }
        });
      });
    }
  });


  /* ═══════════════════════════════════════════════════════════
     8. CHANGE FORM ENHANCEMENTS
     ═══════════════════════════════════════════════════════════ */

  document.addEventListener('DOMContentLoaded', function () {
    // Add floating save bar class to form submit row
    var submitRow = document.querySelector('.submit-row');
    var changeForm = document.querySelector('#content-main form');

    if (submitRow && changeForm) {
      // Wrap submit row for floating behavior
      submitRow.classList.add('ux-floating-save');

      // Add form guard wrapper
      if (typeof Alpine !== 'undefined') {
        changeForm.setAttribute('x-data', 'formGuard');
      }
    }

    // Enhanced fieldset collapse/expand
    var fieldsetHeaders = document.querySelectorAll('.fieldset-header, fieldset h2, .module h2');
    fieldsetHeaders.forEach(function (header) {
      if (header.closest('.collapse')) {
        header.style.cursor = 'pointer';
        header.addEventListener('click', function () {
          var parent = header.closest('.collapse') || header.closest('fieldset');
          if (parent) {
            parent.classList.toggle('collapsed');
          }
        });
      }
    });
  });

})();
