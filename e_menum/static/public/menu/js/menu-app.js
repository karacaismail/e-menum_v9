// ==================== ALPINE.JS MENU APP ====================
// Adapted from menu-v3 for Django integration
// Data source: window.__MENU_DATA__ (injected by Django template)
// ============================================================

function menuApp() {
    return {
        // ==================== STATE ====================
        // UI State
        scrolled: false,
        searchFocused: false,
        searchQuery: '',
        recentSearches: [],
        sidebarCollapsed: false,
        darkMode: false,
        showPhotos: true,
        showPromoBanner: true,
        notificationsOpen: false,
        notifications: [1, 2],

        // Filter State
        activeCategory: 'all',
        quickFilters: { popular: false, discount: false, newItems: false, vegan: false },
        sortBy: 'default',
        priceRange: { min: 0, max: 500 },
        minRating: 0,
        maxCalories: 1500,
        maxPrepTime: 999,
        dietaryFilters: { vegan: false, vegetarian: false, glutenFree: false, spicy: false },
        excludedAllergens: [],
        showFavoritesOnly: false,
        gridColumns: 3,

        // Favorites
        favorites: [],

        // Modal State
        modalOpen: false,
        selectedProduct: null,
        modalOptions: { size: null, extras: [], sauces: [], notes: '', quantity: 1 },

        // Cart State
        cartOpen: false,
        cartItems: [],
        couponCode: '',
        appliedCoupon: null,
        couponDiscount: 0,
        // Storefront Config (from server — admin-managed)
        promoBanner: (window.__MENU_DATA__ && window.__MENU_DATA__.storefront && window.__MENU_DATA__.storefront.promoBanner) || {},
        serverCoupons: (window.__MENU_DATA__ && window.__MENU_DATA__.storefront && window.__MENU_DATA__.storefront.coupons) || {},

        // Theme (read-only, from server)
        layout: (window.__MENU_DATA__ && window.__MENU_DATA__.theme && window.__MENU_DATA__.theme.layout) || 'wide',
        borderRadius: (window.__MENU_DATA__ && window.__MENU_DATA__.theme && window.__MENU_DATA__.theme.borderRadius) || 12,
        themeColors: {
            primary: (window.__MENU_DATA__ && window.__MENU_DATA__.theme && window.__MENU_DATA__.theme.primaryColor) || '#E85D04',
            secondary: (window.__MENU_DATA__ && window.__MENU_DATA__.theme && window.__MENU_DATA__.theme.secondaryColor) || '#1B4332',
            accent: (window.__MENU_DATA__ && window.__MENU_DATA__.theme && window.__MENU_DATA__.theme.accentColor) || '#FFBA08'
        },

        // Toast State
        toasts: [],

        // Data - from Django-injected JSON
        categories: (window.__MENU_DATA__ && window.__MENU_DATA__.categories) || [],
        allergens: (window.__MENU_DATA__ && window.__MENU_DATA__.allergens) || [],
        products: (window.__MENU_DATA__ && window.__MENU_DATA__.products) || [],

        // ==================== INIT ====================
        init() {
            // Load preferences from localStorage
            const savedDarkMode = localStorage.getItem('menuDarkMode');
            if (savedDarkMode) this.darkMode = JSON.parse(savedDarkMode);

            const savedFavorites = localStorage.getItem('menuFavorites');
            if (savedFavorites) this.favorites = JSON.parse(savedFavorites);

            const savedGrid = localStorage.getItem('menuGridColumns');
            if (savedGrid) this.gridColumns = parseInt(savedGrid);

            // Scroll listener
            window.addEventListener('scroll', () => {
                this.scrolled = window.scrollY > 50;
            });

            // Setup category observer
            this.setupCategoryObserver();

            // Watch for changes
            this.$watch('darkMode', (val) => {
                localStorage.setItem('menuDarkMode', JSON.stringify(val));
            });

            this.$watch('gridColumns', (val) => {
                localStorage.setItem('menuGridColumns', val.toString());
            });
        },

        setupCategoryObserver() {
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting && this.activeCategory === 'all') {
                        const id = entry.target.id.replace('section-', '');
                        // Update active category chip visually but don't scroll
                    }
                });
            }, { rootMargin: '-40% 0px -60% 0px' });

            setTimeout(() => {
                this.categories.forEach(cat => {
                    const el = document.getElementById('section-' + cat.id);
                    if (el) observer.observe(el);
                });
            }, 100);
        },

        // ==================== COMPUTED ====================
        get customStyles() {
            return `
                --primary: ${this.themeColors.primary};
                --primary-rgb: ${this.hexToRgb(this.themeColors.primary)};
                --secondary: ${this.themeColors.secondary};
                --accent: ${this.themeColors.accent};
                --radius-md: ${this.borderRadius}px;
                --radius-lg: ${this.borderRadius + 4}px;
                --radius-xl: ${this.borderRadius + 8}px;
            `;
        },

        get cartSubtotal() {
            return this.cartItems.reduce((sum, item) => sum + (item.totalPrice * item.quantity), 0);
        },

        get cartTotal() {
            // Fiyatlar KDV dahil, sadece kupon indirimi dusulur
            return this.cartSubtotal - this.couponDiscount;
        },

        get promoBannerEnabled() {
            return this.promoBanner && this.promoBanner.enabled !== false && this.promoBanner.message;
        },

        get promoBannerMessage() {
            return (this.promoBanner && this.promoBanner.message) || '';
        },

        get promoBannerHighlight() {
            return (this.promoBanner && this.promoBanner.highlight) || '';
        },

        get cartItemCount() {
            return this.cartItems.reduce((sum, item) => sum + item.quantity, 0);
        },

        // ==================== HELPERS ====================
        formatPrice(price) {
            const currency = (window.__MENU_DATA__ && window.__MENU_DATA__.currency) || 'TRY';
            const locale = (window.__MENU_DATA__ && window.__MENU_DATA__.locale) || 'tr-TR';
            return new Intl.NumberFormat(locale, { style: 'currency', currency: currency, minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(price);
        },

        getDiscountedPrice(product) {
            if (product.discount > 0) {
                return product.price * (1 - product.discount / 100);
            }
            return product.price;
        },

        getCategoryCount(categoryId) {
            return this.products.filter(p => p.category === categoryId).length;
        },

        getAllergenName(id) {
            const allergen = this.allergens.find(a => a.id === id);
            return allergen ? allergen.name : id;
        },

        getSortLabel() {
            const t = window.__i18n || {};
            const labels = {
                'default': t.sort_default || 'Sirala',
                'price-low': t.sort_price_low || 'Fiyat: Dusuk',
                'price-high': t.sort_price_high || 'Fiyat: Yuksek',
                'rating': t.sort_rating || 'Puan',
                'popular': t.sort_popular || 'Populer',
                'newest': t.sort_newest || 'En Yeni'
            };
            return labels[this.sortBy] || t.sort_default || 'Sirala';
        },

        getResultsTitle() {
            const t = window.__i18n || {};
            if (this.searchQuery) return `"${this.searchQuery}" icin sonuclar`;
            if (this.showFavoritesOnly) return t.my_favorites || 'Favorilerim';
            if (this.activeCategory !== 'all') {
                const cat = this.categories.find(c => c.id === this.activeCategory);
                return cat ? cat.name : (t.all_products || 'Tum Urunler');
            }
            return t.all_products || 'Tum Urunler';
        },

        getTotalFilteredCount() {
            let count = 0;
            this.categories.forEach(cat => {
                count += this.getFilteredProducts(cat.id).length;
            });
            return count;
        },

        hexToRgb(hex) {
            const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
            return result ? `${parseInt(result[1], 16)}, ${parseInt(result[2], 16)}, ${parseInt(result[3], 16)}` : '232, 93, 4';
        },

        // ==================== SEARCH ====================
        getSearchResults() {
            if (!this.searchQuery) return [];
            const query = this.searchQuery.toLowerCase();
            return this.products.filter(p =>
                p.name.toLowerCase().includes(query) ||
                p.description.toLowerCase().includes(query)
            );
        },

        // ==================== FILTERS ====================
        getFilteredProducts(categoryId) {
            let filtered = this.products.filter(p => p.category === categoryId);

            // Search
            if (this.searchQuery) {
                const query = this.searchQuery.toLowerCase();
                filtered = filtered.filter(p =>
                    p.name.toLowerCase().includes(query) ||
                    p.description.toLowerCase().includes(query)
                );
            }

            // Favorites
            if (this.showFavoritesOnly) {
                filtered = filtered.filter(p => this.favorites.includes(p.id));
            }

            // Quick Filters
            if (this.quickFilters.popular) filtered = filtered.filter(p => p.popular);
            if (this.quickFilters.discount) filtered = filtered.filter(p => p.discount > 0);
            if (this.quickFilters.newItems) filtered = filtered.filter(p => p.isNew);
            if (this.quickFilters.vegan) filtered = filtered.filter(p => p.vegan);

            // Dietary Filters
            if (this.dietaryFilters.vegan) filtered = filtered.filter(p => p.vegan);
            if (this.dietaryFilters.vegetarian) filtered = filtered.filter(p => p.vegetarian);
            if (this.dietaryFilters.glutenFree) filtered = filtered.filter(p => p.glutenFree);
            if (this.dietaryFilters.spicy) filtered = filtered.filter(p => p.spicy);

            // Price Range
            filtered = filtered.filter(p => {
                const price = this.getDiscountedPrice(p);
                return price >= this.priceRange.min && price <= this.priceRange.max;
            });

            // Rating
            if (this.minRating > 0) {
                filtered = filtered.filter(p => p.rating >= this.minRating);
            }

            // Calories
            if (this.maxCalories < 1500) {
                filtered = filtered.filter(p => p.calories <= this.maxCalories);
            }

            // Prep Time
            if (this.maxPrepTime < 999) {
                filtered = filtered.filter(p => p.prepTime <= this.maxPrepTime);
            }

            // Allergens
            if (this.excludedAllergens.length > 0) {
                filtered = filtered.filter(p =>
                    !p.allergens.some(a => this.excludedAllergens.includes(a))
                );
            }

            // Sorting
            switch (this.sortBy) {
                case 'price-low':
                    filtered.sort((a, b) => this.getDiscountedPrice(a) - this.getDiscountedPrice(b));
                    break;
                case 'price-high':
                    filtered.sort((a, b) => this.getDiscountedPrice(b) - this.getDiscountedPrice(a));
                    break;
                case 'rating':
                    filtered.sort((a, b) => b.rating - a.rating);
                    break;
                case 'popular':
                    filtered.sort((a, b) => b.reviews - a.reviews);
                    break;
                case 'newest':
                    filtered.sort((a, b) => (b.isNew ? 1 : 0) - (a.isNew ? 1 : 0));
                    break;
            }

            return filtered;
        },

        shouldShowCategory(categoryId) {
            if (this.activeCategory !== 'all' && this.activeCategory !== categoryId) return false;
            return this.getFilteredProducts(categoryId).length > 0;
        },

        hasActiveFilters() {
            return (
                this.quickFilters.popular || this.quickFilters.discount ||
                this.quickFilters.newItems || this.quickFilters.vegan ||
                this.minRating > 0 || this.excludedAllergens.length > 0 ||
                this.dietaryFilters.vegan || this.dietaryFilters.vegetarian ||
                this.dietaryFilters.glutenFree || this.dietaryFilters.spicy ||
                this.priceRange.min > 0 || this.priceRange.max < 500 ||
                this.maxCalories < 1500 || this.maxPrepTime < 999
            );
        },

        toggleAllergen(id) {
            const index = this.excludedAllergens.indexOf(id);
            if (index > -1) this.excludedAllergens.splice(index, 1);
            else this.excludedAllergens.push(id);
        },

        clearAllFilters() {
            this.searchQuery = '';
            this.quickFilters = { popular: false, discount: false, newItems: false, vegan: false };
            this.sortBy = 'default';
            this.priceRange = { min: 0, max: 500 };
            this.minRating = 0;
            this.maxCalories = 1500;
            this.maxPrepTime = 999;
            this.dietaryFilters = { vegan: false, vegetarian: false, glutenFree: false, spicy: false };
            this.excludedAllergens = [];
            this.showFavoritesOnly = false;
            this.activeCategory = 'all';
            this.showToast((window.__i18n || {}).filters_cleared || 'Filtreler temizlendi', 'success', 'ph-fill ph-check-circle');
        },

        // ==================== NAVIGATION ====================
        scrollToCategory(categoryId) {
            this.activeCategory = categoryId;
            const el = document.getElementById('section-' + categoryId);
            if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
        },

        scrollToTop() {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        },

        // ==================== FAVORITES ====================
        toggleFavorite(productId) {
            const index = this.favorites.indexOf(productId);
            if (index > -1) {
                this.favorites.splice(index, 1);
                this.showToast((window.__i18n || {}).removed_from_favorites || 'Favorilerden kaldirildi', 'warning', 'ph ph-heart-break');
            } else {
                this.favorites.push(productId);
                this.showToast((window.__i18n || {}).added_to_favorites || 'Favorilere eklendi', 'success', 'ph-fill ph-heart');
            }
            localStorage.setItem('menuFavorites', JSON.stringify(this.favorites));
        },

        // ==================== MODAL ====================
        openProductModal(product) {
            this.selectedProduct = product;
            this.modalOptions = {
                size: product.sizes?.[0]?.name || null,
                extras: [],
                sauces: [],
                notes: '',
                quantity: 1
            };
            this.modalOpen = true;
            document.body.style.overflow = 'hidden';
        },

        toggleExtra(name) {
            const index = this.modalOptions.extras.indexOf(name);
            if (index > -1) this.modalOptions.extras.splice(index, 1);
            else this.modalOptions.extras.push(name);
        },

        toggleSauce(sauce) {
            const index = this.modalOptions.sauces.indexOf(sauce);
            if (index > -1) this.modalOptions.sauces.splice(index, 1);
            else this.modalOptions.sauces.push(sauce);
        },

        getModalTotal() {
            if (!this.selectedProduct) return 0;
            let total = this.getDiscountedPrice(this.selectedProduct);

            if (this.modalOptions.size && this.selectedProduct.sizes) {
                const size = this.selectedProduct.sizes.find(s => s.name === this.modalOptions.size);
                if (size) total += size.price;
            }

            if (this.selectedProduct.extras) {
                this.modalOptions.extras.forEach(name => {
                    const extra = this.selectedProduct.extras.find(e => e.name === name);
                    if (extra) total += extra.price;
                });
            }

            return total;
        },

        // ==================== CART ====================
        addToCart() {
            const item = {
                cartId: Date.now(),
                id: this.selectedProduct.id,
                name: this.selectedProduct.name,
                image: this.selectedProduct.image,
                basePrice: this.getDiscountedPrice(this.selectedProduct),
                totalPrice: this.getModalTotal(),
                quantity: this.modalOptions.quantity,
                size: this.modalOptions.size,
                extras: [...this.modalOptions.extras],
                sauces: [...this.modalOptions.sauces],
                notes: this.modalOptions.notes
            };

            this.cartItems.push(item);
            this.modalOpen = false;
            document.body.style.overflow = '';
            this.showToast(`${this.selectedProduct.name} ${(window.__i18n || {}).added_to_cart || 'sepete eklendi!'}`, 'success', 'ph-fill ph-shopping-bag');
        },

        isInCart(productId) {
            return this.cartItems.some(item => item.id === productId);
        },

        getCartQuantity(productId) {
            return this.cartItems.filter(item => item.id === productId).reduce((sum, item) => sum + item.quantity, 0);
        },

        incrementCartItem(productId) {
            const item = this.cartItems.find(i => i.id === productId);
            if (item) item.quantity++;
        },

        decrementCartItem(productId) {
            const item = this.cartItems.find(i => i.id === productId);
            if (item) {
                item.quantity--;
                if (item.quantity <= 0) {
                    this.cartItems = this.cartItems.filter(i => i.id !== productId);
                }
            }
        },

        updateItemQty(cartId, delta) {
            const item = this.cartItems.find(i => i.cartId === cartId);
            if (item) {
                item.quantity += delta;
                if (item.quantity <= 0) this.removeItem(cartId);
            }
        },

        removeItem(cartId) {
            const item = this.cartItems.find(i => i.cartId === cartId);
            this.cartItems = this.cartItems.filter(i => i.cartId !== cartId);
            if (item) this.showToast(`${item.name} ${(window.__i18n || {}).removed_from_cart || 'sepetten kaldirildi'}`, 'warning', 'ph ph-trash');
        },

        formatItemOptions(item) {
            const parts = [];
            if (item.size) parts.push(item.size);
            if (item.extras?.length) parts.push(item.extras.join(', '));
            if (item.sauces?.length) parts.push(item.sauces.join(', '));
            return parts.join(' \u2022 ') || (window.__i18n || {}).standard || 'Standart';
        },

        applyCoupon() {
            if (!this.couponCode.trim()) return;
            const code = this.couponCode.toUpperCase().trim();

            // Use server-provided coupons if available, otherwise use defaults
            const coupons = Object.keys(this.serverCoupons).length > 0
                ? this.serverCoupons
                : {
                    'HOSGELDIN': { discount: 20, type: 'percent', name: '%20 Hosgeldin Indirimi' },
                    'LEZZET50': { discount: 50, type: 'fixed', name: '50\u20BA Indirim' },
                    'TATLI10': { discount: 10, type: 'percent', name: '%10 Indirim' }
                };

            if (coupons[code]) {
                const coupon = coupons[code];
                this.couponDiscount = coupon.type === 'percent'
                    ? this.cartSubtotal * (coupon.discount / 100)
                    : coupon.discount;
                this.appliedCoupon = coupon.name;
                this.showToast(`${(window.__i18n || {}).coupon_applied || 'Kupon uygulandi'}: ${coupon.name}`, 'success', 'ph-fill ph-ticket');
            } else {
                this.showToast((window.__i18n || {}).coupon_invalid || 'Gecersiz kupon kodu', 'error', 'ph ph-x-circle');
            }
            this.couponCode = '';
        },

        removeCoupon() {
            this.appliedCoupon = null;
            this.couponDiscount = 0;
            this.showToast((window.__i18n || {}).coupon_removed || 'Kupon kaldirildi', 'warning', 'ph ph-ticket');
        },

        // ==================== TOAST ====================
        showToast(message, type = 'success', icon = 'ph-fill ph-check-circle') {
            const toast = { id: Date.now(), message, type, icon };
            this.toasts.push(toast);
            setTimeout(() => {
                this.toasts = this.toasts.filter(t => t.id !== toast.id);
            }, 3500);
        },

        removeToast(id) {
            this.toasts = this.toasts.filter(t => t.id !== id);
        }
    };
}
