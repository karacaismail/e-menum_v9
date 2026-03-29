/**
 * E-Menum Dashboard — Mainboard Controller
 *
 * Handles: data fetching, chart rendering, auto-refresh,
 * command palette, and error states.
 *
 * Design principles:
 * - Each card is independently loaded (Promise.all for parallelism)
 * - AbortController cancels in-flight requests on range change
 * - ECharts instances tracked for resize & disposal
 * - ResizeObserver per chart for responsive behavior
 */
(function () {
    'use strict';

    /* ═══════════════════════════════════════════════════
       DashboardLoader
       ═══════════════════════════════════════════════════ */

    class DashboardLoader {
        constructor() {
            this.dateRange = '30d';
            this.charts = {};
            this.abortController = null;
            this.refreshTimer = null;
            this.leafletMap = null;
            this.resizeObservers = [];
        }

        init() {
            // Range selector
            const rangeSelect = document.getElementById('dateRangeSelect');
            if (rangeSelect) {
                rangeSelect.addEventListener('change', (e) => {
                    this.dateRange = e.target.value;
                    this.reloadAll();
                });
            }

            // Refresh button
            const refreshBtn = document.getElementById('refreshBtn');
            if (refreshBtn) {
                refreshBtn.addEventListener('click', () => {
                    refreshBtn.classList.add('spinning');
                    this.reloadAll().then(() => {
                        setTimeout(() => refreshBtn.classList.remove('spinning'), 300);
                    });
                });
            }

            // Load all cards
            this.loadAllCards();

            // Auto-refresh
            this.setupAutoRefresh();

            // Command palette
            this.setupCommandPalette();

            // Keyboard shortcuts
            this.setupKeyboardShortcuts();
        }

        async loadAllCards() {
            // Cancel previous
            if (this.abortController) this.abortController.abort();
            this.abortController = new AbortController();

            const cards = document.querySelectorAll('[data-endpoint]');
            const promises = Array.from(cards).map(card => this.loadCard(card));
            await Promise.allSettled(promises);
        }

        async reloadAll() {
            // Dispose all charts
            Object.values(this.charts).forEach(c => {
                try { c.dispose(); } catch(e) {}
            });
            this.charts = {};

            if (this.leafletMap) {
                try { this.leafletMap.remove(); } catch(e) {}
                this.leafletMap = null;
            }

            // Re-show skeletons
            document.querySelectorAll('[data-endpoint]').forEach(card => {
                const body = card.querySelector('.chart-body') || card;
                body.classList.add('loading');
            });

            await this.loadAllCards();
        }

        async loadCard(cardEl) {
            const endpoint = cardEl.dataset.endpoint;
            const chartType = cardEl.dataset.chartType;
            const body = cardEl.querySelector('.chart-body') || cardEl;
            const url = endpoint + (endpoint.includes('?') ? '&' : '?') + 'range=' + this.dateRange;

            try {
                const resp = await fetch(url, {
                    signal: this.abortController.signal,
                    headers: { 'X-Requested-With': 'XMLHttpRequest' }
                });

                if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
                const json = await resp.json();

                if (!json.success) throw new Error(json.error || 'API error');

                body.classList.remove('loading');
                this.renderCard(cardEl, json.data, chartType);
            } catch (err) {
                if (err.name === 'AbortError') return;
                console.error(`Failed to load ${endpoint}:`, err);
                body.classList.remove('loading');
                this.showError(body, endpoint);
            }
        }

        showError(container, endpoint) {
            container.innerHTML = `
                <div class="card-error">
                    <i class="ph ph-warning-circle"></i>
                    <span>${this._t('errorLoading', 'Veri yüklenemedi')}</span>
                    <button class="card-error-retry" onclick="window._dashboard.loadCard(this.closest('[data-endpoint]'))">
                        ${this._t('retryBtn', 'Yeniden dene')} →
                    </button>
                </div>
            `;
        }

        /* ═══ Renderers ═══ */

        renderCard(cardEl, data, chartType) {
            switch (chartType) {
                case 'kpi':      this.renderKPIStrip(cardEl, data); break;
                case 'line':     this.renderLineChart(cardEl, data); break;
                case 'heatmap':  this.renderHeatmap(cardEl, data); break;
                case 'pie':      this.renderDonut(cardEl, data); break;
                case 'funnel':   this.renderFunnel(cardEl, data); break;
                case 'map':      this.renderLeafletMap(cardEl, data); break;
                case 'table':    this.renderActivityTable(cardEl, data); break;
                case 'insights': this.renderInsights(cardEl, data); break;
            }
        }

        renderKPIStrip(stripEl, data) {
            const kpiKeys = ['organizations', 'qr_scans', 'active_menus', 'pending_requests', 'mrr', 'trial_count'];
            const cards = stripEl.querySelectorAll('.kpi-card');

            kpiKeys.forEach((key, idx) => {
                const card = cards[idx];
                if (!card || !data[key]) return;

                const kpi = data[key];
                card.classList.remove('loading');

                // Icon
                const iconEl = card.querySelector('.kpi-icon');
                if (iconEl) {
                    iconEl.innerHTML = `<i class="ph ph-${kpi.icon || 'chart-bar'}"></i>`;
                }

                // Value with animation
                const valueEl = card.querySelector('.kpi-value');
                if (valueEl) {
                    const target = kpi.format === 'currency'
                        ? '₺' + this.formatNumber(kpi.value)
                        : this.formatNumber(kpi.value);
                    this.animateValue(valueEl, target, kpi.value);
                }

                // Label
                const labelEl = card.querySelector('.kpi-label');
                if (labelEl) labelEl.textContent = kpi.label;

                // Trend
                const trendEl = card.querySelector('.kpi-trend');
                if (trendEl) {
                    const change = kpi.change || 0;
                    const cls = change > 0 ? 'up' : change < 0 ? 'down' : 'neutral';
                    const arrow = change > 0 ? '↑' : change < 0 ? '↓' : '→';
                    trendEl.className = `kpi-trend ${cls}`;
                    trendEl.innerHTML = `<span>${arrow} ${Math.abs(change).toFixed(1)}%</span>`;
                }

                // Sparkline
                const sparkEl = card.querySelector('.kpi-sparkline');
                if (sparkEl && kpi.trend && kpi.trend.length > 0) {
                    const chartId = `sparkline-${idx}`;
                    sparkEl.id = chartId;
                    const chart = echarts.init(sparkEl, 'emenum');
                    this.charts[chartId] = chart;

                    const color = (kpi.change || 0) >= 0 ? '#6366f1' : '#EF4444';
                    chart.setOption({
                        grid: { top: 2, right: 2, bottom: 2, left: 2 },
                        xAxis: { type: 'category', show: false, data: kpi.trend.map((_, i) => i) },
                        yAxis: { type: 'value', show: false },
                        series: [{
                            type: 'line', data: kpi.trend, smooth: true,
                            symbol: 'none', lineStyle: { width: 1.5, color },
                            areaStyle: { opacity: 0.1, color }
                        }]
                    });
                }
            });
        }

        renderLineChart(cardEl, data) {
            const body = cardEl.querySelector('.chart-body');
            if (!body) return;

            // Update subtitle with total
            const subtitle = cardEl.querySelector('[data-total]');
            if (subtitle && data.total !== undefined) {
                subtitle.textContent = `Toplam: ${this.formatNumber(data.total)}`;
            }

            const chartEl = document.createElement('div');
            chartEl.style.width = '100%';
            chartEl.style.height = '260px';
            body.innerHTML = '';
            body.appendChild(chartEl);

            const chart = echarts.init(chartEl, 'emenum');
            this.charts['qr-trend'] = chart;

            chart.setOption({
                grid: { top: 8, right: 8, bottom: 24, left: 48 },
                tooltip: { trigger: 'axis' },
                xAxis: {
                    type: 'category',
                    data: (data.dates || []).map(d => {
                        const dt = new Date(d);
                        return `${dt.getDate()}/${dt.getMonth() + 1}`;
                    }),
                    boundaryGap: false,
                },
                yAxis: { type: 'value' },
                series: [{
                    type: 'line', data: data.values || [],
                    smooth: true, symbol: 'none',
                    lineStyle: { width: 2, color: '#6366f1' },
                    areaStyle: { opacity: 0.12, color: '#6366f1' }
                }]
            });

            this.observeResize(chartEl, chart);
        }

        renderHeatmap(cardEl, data) {
            const body = cardEl.querySelector('.chart-body');
            if (!body || !data || data.length === 0) {
                body.innerHTML = `<div class="card-error"><i class="ph ph-chart-bar"></i><span>${this._t('heatmapNoData', 'Heatmap verisi yok')}</span></div>`;
                return;
            }

            const chartEl = document.createElement('div');
            chartEl.style.width = '100%';
            chartEl.style.height = '260px';
            body.innerHTML = '';
            body.appendChild(chartEl);

            // Flatten data
            const orgNames = data.map(d => d.org_name);
            const allData = [];
            let maxVal = 1;

            data.forEach((org, yIdx) => {
                (org.data || []).forEach(([week, day, count]) => {
                    allData.push([week, yIdx, count]);
                    if (count > maxVal) maxVal = count;
                });
            });

            const chart = echarts.init(chartEl, 'emenum');
            this.charts['heatmap'] = chart;

            chart.setOption({
                grid: { top: 8, right: 30, bottom: 24, left: 120 },
                tooltip: {
                    formatter: function(p) {
                        return `${orgNames[p.value[1]] || ''}: ${p.value[2]} tarama`;
                    }
                },
                xAxis: {
                    type: 'category',
                    data: Array.from({length: 12}, (_, i) => `H${i + 1}`),
                    splitArea: { show: true }
                },
                yAxis: {
                    type: 'category',
                    data: orgNames,
                    axisLabel: {
                        fontSize: 11,
                        formatter: function(v) { return v.length > 18 ? v.slice(0, 18) + '…' : v; }
                    }
                },
                visualMap: {
                    min: 0, max: maxVal,
                    calculable: true, orient: 'vertical', right: 0, top: 'center',
                    inRange: { color: ['#1F2937', '#374151', '#6366f1'] },
                    textStyle: { color: '#6B7280', fontSize: 10 }
                },
                series: [{
                    type: 'heatmap', data: allData,
                    label: { show: false },
                    emphasis: { itemStyle: { shadowBlur: 6, shadowColor: 'rgba(0,0,0,0.5)' } }
                }]
            });

            this.observeResize(chartEl, chart);
        }

        renderDonut(cardEl, data) {
            const body = cardEl.querySelector('.chart-body');
            if (!body) return;

            const chartEl = document.createElement('div');
            chartEl.style.width = '100%';
            chartEl.style.height = '260px';
            body.innerHTML = '';
            body.appendChild(chartEl);

            const total = (data || []).reduce((s, d) => s + d.value, 0);
            const chart = echarts.init(chartEl, 'emenum');
            this.charts['donut'] = chart;

            chart.setOption({
                tooltip: {
                    trigger: 'item',
                    formatter: '{b}: {c} ({d}%)'
                },
                legend: {
                    orient: 'horizontal', bottom: 0,
                    textStyle: { color: '#9CA3AF', fontSize: 11 }
                },
                graphic: [{
                    type: 'text',
                    left: 'center', top: '40%',
                    style: {
                        text: String(total), fill: '#F9FAFB',
                        fontSize: 28, fontWeight: 700,
                        textAlign: 'center', fontFamily: 'Inter'
                    }
                }, {
                    type: 'text',
                    left: 'center', top: '52%',
                    style: {
                        text: 'toplam', fill: '#6B7280',
                        fontSize: 12, textAlign: 'center', fontFamily: 'Inter'
                    }
                }],
                series: [{
                    type: 'pie',
                    radius: ['55%', '75%'],
                    center: ['50%', '45%'],
                    avoidLabelOverlap: false,
                    label: { show: false },
                    emphasis: { label: { show: false } },
                    data: data || []
                }]
            });

            this.observeResize(chartEl, chart);
        }

        renderFunnel(cardEl, data) {
            const body = cardEl.querySelector('.chart-body');
            if (!body) return;

            const chartEl = document.createElement('div');
            chartEl.style.width = '100%';
            chartEl.style.height = '260px';
            body.innerHTML = '';
            body.appendChild(chartEl);

            const chart = echarts.init(chartEl, 'emenum');
            this.charts['funnel'] = chart;

            chart.setOption({
                tooltip: {
                    trigger: 'item',
                    formatter: function(p) {
                        const prev = p.dataIndex > 0 ? data[p.dataIndex - 1].count : null;
                        let rate = prev ? ((p.value / prev) * 100).toFixed(1) + '%' : '—';
                        return `${p.name}: ${p.value}<br>Dönüşüm: ${rate}`;
                    }
                },
                series: [{
                    type: 'funnel',
                    left: '10%', right: '10%', top: 20, bottom: 20,
                    sort: 'descending',
                    gap: 4,
                    label: {
                        show: true,
                        position: 'inside',
                        formatter: '{b}\n{c}',
                        color: '#F9FAFB',
                        fontSize: 13,
                        fontWeight: 500
                    },
                    itemStyle: { borderWidth: 0 },
                    emphasis: { label: { fontSize: 14 } },
                    data: (data || []).map((d, i) => ({
                        name: d.step,
                        value: d.count,
                        itemStyle: {
                            color: ['#6366f1', '#818cf8', '#a5b4fc', '#c7d2fe'][i] || '#6366f1'
                        }
                    }))
                }]
            });

            this.observeResize(chartEl, chart);
        }

        renderLeafletMap(cardEl, data) {
            const body = cardEl.querySelector('.chart-body');
            if (!body) return;

            const mapEl = document.createElement('div');
            mapEl.setAttribute('data-leaflet', 'true');
            mapEl.style.width = '100%';
            mapEl.style.height = '320px';
            mapEl.style.borderRadius = '8px';
            mapEl.style.overflow = 'hidden';
            body.innerHTML = '';
            body.appendChild(mapEl);

            if (typeof L === 'undefined') {
                body.innerHTML = `<div class="card-error"><i class="ph ph-map-pin"></i><span>${this._t('leafletFailed', 'Leaflet yüklenemedi')}</span></div>`;
                return;
            }

            const map = L.map(mapEl, { zoomControl: true, attributionControl: false })
                .setView([39.0, 35.0], 6);

            L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
                subdomains: 'abcd', maxZoom: 19
            }).addTo(map);

            this.leafletMap = map;

            (data || []).forEach(item => {
                const radius = Math.max(5, Math.sqrt(item.count) * 3);
                L.circleMarker([item.lat, item.lng], {
                    radius, fillColor: '#6366f1', color: '#818cf8',
                    weight: 1, opacity: 0.8, fillOpacity: 0.6
                })
                .bindTooltip(`<strong>${item.city}</strong><br>${item.count} işletme`, {
                    className: 'leaflet-dark-tooltip'
                })
                .addTo(map);
            });

            // Invalidate size after render
            setTimeout(() => map.invalidateSize(), 200);
        }

        renderActivityTable(cardEl, data) {
            const body = cardEl.querySelector('.chart-body');
            if (!body) return;

            if (!data || data.length === 0) {
                body.innerHTML = `<div class="card-error"><i class="ph ph-clock"></i><span>${this._t('noActivity', 'Henüz aktivite yok')}</span></div>`;
                return;
            }

            const actionLabels = { add: 'Ekleme', change: 'Değişiklik', delete: 'Silme' };
            const rows = data.map(entry => {
                const timeAgo = this.timeAgo(entry.timestamp);
                const objLink = entry.url
                    ? `<a href="${entry.url}" class="activity-object">${this.escHtml(entry.object_repr)}</a>`
                    : `<span class="activity-object">${this.escHtml(entry.object_repr)}</span>`;

                return `<tr>
                    <td><span class="activity-badge ${entry.action}">${actionLabels[entry.action] || entry.action}</span></td>
                    <td><div class="activity-user"><div class="activity-avatar">${this.escHtml(entry.user_initial)}</div><span>${this.escHtml(entry.user)}</span></div></td>
                    <td>${objLink}</td>
                    <td><span class="activity-model">${this.escHtml(entry.app)}.${this.escHtml(entry.model)}</span></td>
                    <td><span class="activity-time">${timeAgo}</span></td>
                </tr>`;
            }).join('');

            body.innerHTML = `
                <table class="activity-table">
                    <thead>
                        <tr>
                            <th>İşlem</th>
                            <th>Kullanıcı</th>
                            <th>Nesne</th>
                            <th>Model</th>
                            <th>Zaman</th>
                        </tr>
                    </thead>
                    <tbody>${rows}</tbody>
                </table>
            `;
        }

        renderInsights(cardEl, data) {
            const body = cardEl.querySelector('.chart-body') || cardEl.querySelector('.insights-body');
            if (!body) return;

            if (!data || data.length === 0) {
                body.innerHTML = `
                    <div class="insights-empty">
                        <i class="ph ph-check-circle"></i>
                        <span>${this._t('noInsights', 'Şu an aktif içgörü yok')}</span>
                    </div>
                `;
                return;
            }

            const iconMap = {
                warning: 'ph-warning-circle',
                opportunity: 'ph-rocket',
                info: 'ph-info',
                success: 'ph-check-circle'
            };

            body.innerHTML = data.map(insight => {
                const icon = iconMap[insight.type] || 'ph-info';
                const metric = insight.metric_value
                    ? `<span class="insight-metric">${insight.metric_value} ${insight.metric_label || ''}</span>`
                    : '';
                const action = insight.action_url
                    ? `<a href="${insight.action_url}" class="insight-action">${insight.action_label || 'Detay'} →</a>`
                    : '';

                return `
                    <div class="insight-item ${insight.type}">
                        <div class="insight-header">
                            <i class="ph ${icon} insight-icon ${insight.type}"></i>
                            <span class="insight-title">${this.escHtml(insight.title)}</span>
                        </div>
                        <div class="insight-body">${this.escHtml(insight.body)}</div>
                        <div class="insight-footer">${metric}${action}</div>
                    </div>
                `;
            }).join('');
        }

        /* ═══ Command Palette ═══ */

        setupCommandPalette() {
            const overlay = document.getElementById('commandPalette');
            const input = document.getElementById('cmdPaletteInput');
            const results = document.getElementById('cmdPaletteResults');
            if (!overlay || !input) return;

            let debounceTimer = null;
            let focusedIdx = -1;

            const open = () => {
                overlay.style.display = 'block';
                input.value = '';
                input.focus();
                focusedIdx = -1;
                results.innerHTML = `<div class="cmd-palette-empty"><i class="ph ph-magnifying-glass"></i><span>${this._t('searchMinChars', 'Aramak için en az 2 karakter yazın')}</span></div>`;
            };

            const close = () => {
                overlay.style.display = 'none';
                input.value = '';
            };

            // Backdrop click
            overlay.querySelector('.cmd-palette-backdrop').addEventListener('click', close);

            // Input handler
            input.addEventListener('input', () => {
                clearTimeout(debounceTimer);
                const q = input.value.trim();
                if (q.length < 2) {
                    results.innerHTML = `<div class="cmd-palette-empty"><i class="ph ph-magnifying-glass"></i><span>${this._t('searchMinChars', 'Aramak için en az 2 karakter yazın')}</span></div>`;
                    return;
                }

                results.innerHTML = `<div class="cmd-palette-loading"><i class="ph ph-spinner"></i> ${this._t('searching', 'Aranıyor...')}</div>`;

                debounceTimer = setTimeout(async () => {
                    try {
                        const resp = await fetch(`/admin/api/search/?q=${encodeURIComponent(q)}`, {
                            headers: { 'X-Requested-With': 'XMLHttpRequest' }
                        });
                        const json = await resp.json();
                        if (!json.success) throw new Error('Search failed');
                        this.renderSearchResults(results, json.data.groups);
                        focusedIdx = -1;
                    } catch (e) {
                        results.innerHTML = `<div class="cmd-palette-empty"><i class="ph ph-warning-circle"></i><span>${this._t('searchFailed', 'Arama başarısız')}</span></div>`;
                    }
                }, 250);
            });

            // Keyboard nav
            input.addEventListener('keydown', (e) => {
                const items = results.querySelectorAll('.cmd-palette-item');
                if (e.key === 'Escape') { close(); return; }
                if (e.key === 'ArrowDown') {
                    e.preventDefault();
                    focusedIdx = Math.min(focusedIdx + 1, items.length - 1);
                    this.updateFocus(items, focusedIdx);
                }
                if (e.key === 'ArrowUp') {
                    e.preventDefault();
                    focusedIdx = Math.max(focusedIdx - 1, 0);
                    this.updateFocus(items, focusedIdx);
                }
                if (e.key === 'Enter' && focusedIdx >= 0 && items[focusedIdx]) {
                    e.preventDefault();
                    window.location.href = items[focusedIdx].href;
                }
            });

            // Global shortcut: Cmd+K / Ctrl+K
            document.addEventListener('keydown', (e) => {
                if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
                    e.preventDefault();
                    if (overlay.style.display === 'block') close();
                    else open();
                }
                if (e.key === 'Escape' && overlay.style.display === 'block') {
                    close();
                }
            });
        }

        renderSearchResults(container, groups) {
            if (!groups || groups.length === 0) {
                container.innerHTML = `<div class="cmd-palette-empty"><i class="ph ph-magnifying-glass"></i><span>${this._t('noResults', 'Sonuç bulunamadı')}</span></div>`;
                return;
            }

            container.innerHTML = groups.map(group => {
                const items = group.items.map(item => `
                    <a href="${item.url}" class="cmd-palette-item">
                        <div class="cmd-palette-item-icon"><i class="ph ph-${group.icon || 'dot'}"></i></div>
                        <div class="cmd-palette-item-text">
                            <div class="cmd-palette-item-title">${this.escHtml(item.title)}</div>
                            <div class="cmd-palette-item-subtitle">${this.escHtml(item.subtitle || '')}</div>
                        </div>
                    </a>
                `).join('');

                return `
                    <div class="cmd-palette-group-label">
                        <i class="ph ph-${group.icon || 'dot'}"></i>
                        ${this.escHtml(group.label)}
                    </div>
                    ${items}
                `;
            }).join('');
        }

        updateFocus(items, idx) {
            items.forEach((el, i) => {
                el.classList.toggle('focused', i === idx);
            });
            if (items[idx]) items[idx].scrollIntoView({ block: 'nearest' });
        }

        /* ═══ Auto-Refresh ═══ */

        setupAutoRefresh() {
            // Refresh every 5 minutes
            this.refreshTimer = setInterval(() => {
                if (!document.hidden) this.reloadAll();
            }, 5 * 60 * 1000);

            // Refresh on tab focus after being hidden
            document.addEventListener('visibilitychange', () => {
                if (!document.hidden) this.reloadAll();
            });
        }

        /* ═══ Keyboard Shortcuts ═══ */

        setupKeyboardShortcuts() {
            let gPressed = false;
            let gTimer = null;

            document.addEventListener('keydown', (e) => {
                // Don't trigger in inputs
                if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT') return;

                if (e.key === 'g' && !e.metaKey && !e.ctrlKey) {
                    if (!gPressed) {
                        gPressed = true;
                        clearTimeout(gTimer);
                        gTimer = setTimeout(() => { gPressed = false; }, 500);
                    }
                    return;
                }

                if (gPressed) {
                    gPressed = false;
                    clearTimeout(gTimer);
                    if (e.key === 'd') { window.location.href = '/admin/dashboard/'; return; }
                    if (e.key === 'o') { window.location.href = '/admin/core/organization/'; return; }
                    if (e.key === 'm') { window.location.href = '/admin/menu/menu/'; return; }
                    if (e.key === 'u') { window.location.href = '/admin/core/user/'; return; }
                }
            });
        }

        /* ═══ Utilities ═══ */

        observeResize(el, chart) {
            if (typeof ResizeObserver === 'undefined') return;
            const ro = new ResizeObserver(() => {
                try { chart.resize(); } catch(e) {}
            });
            ro.observe(el.parentElement || el);
            this.resizeObservers.push(ro);
        }

        formatNumber(num) {
            if (num === null || num === undefined) return '0';
            const n = Number(num);
            if (isNaN(n)) return '0';
            if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M';
            if (n >= 1000) return (n / 1000).toFixed(1) + 'K';
            return n.toLocaleString('tr-TR');
        }

        animateValue(el, displayText, numericValue) {
            const duration = 600;
            const target = Number(numericValue) || 0;
            const isCurrency = displayText.startsWith('₺');
            const start = performance.now();

            const animate = (now) => {
                const progress = Math.min((now - start) / duration, 1);
                const eased = 1 - Math.pow(1 - progress, 3); // easeOutCubic
                const current = Math.round(target * eased);

                if (isCurrency) {
                    el.textContent = '₺' + this.formatNumber(current);
                } else {
                    el.textContent = this.formatNumber(current);
                }

                if (progress < 1) requestAnimationFrame(animate);
                else el.textContent = displayText;
            };

            if (target > 0) requestAnimationFrame(animate);
            else el.textContent = displayText;
        }

        timeAgo(isoString) {
            const now = Date.now();
            const then = new Date(isoString).getTime();
            const diff = Math.floor((now - then) / 1000);

            if (diff < 60) return this._t('timeJustNow', 'az önce');
            if (diff < 3600) return `${Math.floor(diff / 60)} ${this._t('timeMinAgo', 'dk önce')}`;
            if (diff < 86400) return `${Math.floor(diff / 3600)} ${this._t('timeHourAgo', 'saat önce')}`;
            if (diff < 604800) return `${Math.floor(diff / 86400)} ${this._t('timeDayAgo', 'gün önce')}`;
            return new Date(isoString).toLocaleDateString(document.documentElement.lang || 'tr-TR');
        }

        escHtml(str) {
            if (!str) return '';
            const div = document.createElement('div');
            div.textContent = str;
            return div.innerHTML;
        }

        /**
         * Return a translated string from window.DashboardI18n,
         * falling back to the provided default if the key is missing.
         */
        _t(key, fallback) {
            return (window.DashboardI18n && window.DashboardI18n[key]) || fallback;
        }
    }

    /* ═══ Initialize ═══ */
    document.addEventListener('DOMContentLoaded', () => {
        window._dashboard = new DashboardLoader();
        window._dashboard.init();
    });

})();
