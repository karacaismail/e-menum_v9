/**
 * E-Menum ECharts Dark Theme
 *
 * Register with: echarts.registerTheme('emenum', ...)
 * Use with:      echarts.init(el, 'emenum')
 */
(function () {
    'use strict';

    var theme = {
        backgroundColor: 'transparent',

        color: [
            '#6366f1', '#3B82F6', '#8B5CF6', '#F59E0B',
            '#EF4444', '#06B6D4', '#EC4899', '#84CC16'
        ],

        textStyle: {
            color: '#9CA3AF',
            fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, system-ui, sans-serif"
        },

        title: {
            textStyle: { color: '#F9FAFB', fontWeight: 600 },
            subtextStyle: { color: '#6B7280' }
        },

        tooltip: {
            backgroundColor: '#1F2937',
            borderColor: '#374151',
            borderWidth: 1,
            textStyle: { color: '#F9FAFB', fontSize: 13 },
            extraCssText: 'border-radius: 8px; box-shadow: 0 8px 24px rgba(0,0,0,0.4);'
        },

        legend: {
            textStyle: { color: '#9CA3AF', fontSize: 12 },
            pageTextStyle: { color: '#9CA3AF' },
            pageIconColor: '#9CA3AF',
            pageIconInactiveColor: '#374151'
        },

        categoryAxis: {
            axisLine: { lineStyle: { color: '#374151' } },
            axisTick: { lineStyle: { color: '#374151' } },
            axisLabel: { color: '#6B7280', fontSize: 11 },
            splitLine: { lineStyle: { color: '#374151', opacity: 0.3 } }
        },

        valueAxis: {
            axisLine: { lineStyle: { color: '#374151' } },
            axisTick: { lineStyle: { color: '#374151' } },
            axisLabel: { color: '#6B7280', fontSize: 11 },
            splitLine: { lineStyle: { color: '#374151', opacity: 0.3 } }
        },

        line: {
            smooth: true,
            symbol: 'circle',
            symbolSize: 4,
            lineStyle: { width: 2 }
        },

        bar: {
            barMaxWidth: 30,
            itemStyle: { borderRadius: [4, 4, 0, 0] }
        },

        pie: {
            itemStyle: { borderWidth: 2, borderColor: '#1F2937' }
        },

        funnel: {
            itemStyle: { borderWidth: 0 }
        },

        visualMap: {
            textStyle: { color: '#9CA3AF' },
            inRange: {
                color: ['#1F2937', '#374151', '#6366f1']
            }
        }
    };

    if (typeof echarts !== 'undefined') {
        echarts.registerTheme('emenum', theme);
    }
})();
