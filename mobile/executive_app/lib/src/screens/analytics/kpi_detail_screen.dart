import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shared_core/shared_core.dart';
import '../../providers/analytics_provider.dart';
import '../../widgets/trend_indicator.dart';

class KpiDetailScreen extends StatefulWidget {
  const KpiDetailScreen({super.key});

  @override
  State<KpiDetailScreen> createState() => _KpiDetailScreenState();
}

class _KpiDetailScreenState extends State<KpiDetailScreen> {
  String _selectedPeriod = 'year';

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<AnalyticsProvider>().fetchKpiTrends(_selectedPeriod);
    });
  }

  @override
  Widget build(BuildContext context) {
    final analytics = context.watch<AnalyticsProvider>();

    return Scaffold(
      appBar: AppBar(
        title: const Text('KPI Trends'),
        actions: [
          PopupMenuButton<String>(
            icon: const Icon(Icons.calendar_today),
            onSelected: (period) {
              setState(() => _selectedPeriod = period);
              context.read<AnalyticsProvider>().fetchKpiTrends(period);
            },
            itemBuilder: (_) => [
              const PopupMenuItem(value: 'month', child: Text('This Month')),
              const PopupMenuItem(value: 'quarter', child: Text('This Quarter')),
              const PopupMenuItem(value: 'year', child: Text('This Year')),
            ],
          ),
        ],
      ),
      body: analytics.isLoading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _buildChartPlaceholder('Revenue Trend', Icons.show_chart),
                  const SizedBox(height: 16),
                  _buildChartPlaceholder('Profit Trend', Icons.trending_up),
                  const SizedBox(height: 16),
                  _buildChartPlaceholder('Orders Trend', Icons.shopping_cart),
                  const SizedBox(height: 24),
                  Text('Key Metrics', style: AppTextStyles.titleLarge),
                  const SizedBox(height: 12),
                  _buildMetricsRow(),
                  const SizedBox(height: 24),
                  Text('Monthly Breakdown', style: AppTextStyles.titleLarge),
                  const SizedBox(height: 12),
                  ..._buildMonthlyList(analytics.kpiTrends),
                ],
              ),
            ),
    );
  }

  Widget _buildChartPlaceholder(String label, IconData icon) {
    return Card(
      margin: EdgeInsets.zero,
      child: Container(
        height: 180,
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(label, style: AppTextStyles.titleMedium),
            const Spacer(),
            Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(icon, size: 48, color: AppColors.textHint),
                  const SizedBox(height: 8),
                  Text('Chart placeholder', style: AppTextStyles.bodySmall),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMetricsRow() {
    final latest = analytics.kpiTrends.isNotEmpty
        ? analytics.kpiTrends.last
        : <String, dynamic>{};
    final previous = analytics.kpiTrends.length > 1
        ? analytics.kpiTrends[analytics.kpiTrends.length - 2]
        : <String, dynamic>{};

    final currentValue = (latest['revenue'] ?? 0).toDouble();
    final prevValue = (previous['revenue'] ?? 0).toDouble();
    final growth = prevValue > 0
        ? ((currentValue - prevValue) / prevValue) * 100
        : 0.0;
    final target = (latest['target'] ?? currentValue).toDouble();
    final vsLastPeriod = currentValue - prevValue;

    return Row(
      children: [
        _buildMetricCard('Current', '\$${_formatValue(currentValue)}'),
        const SizedBox(width: 8),
        _buildMetricCard('Growth', '${growth.toStringAsFixed(1)}%'),
        const SizedBox(width: 8),
        _buildMetricCard('Target', '\$${_formatValue(target)}'),
        const SizedBox(width: 8),
        _buildMetricCard('vs Last', '${vsLastPeriod >= 0 ? '+' : ''}\$${_formatValue(vsLastPeriod)}'),
      ],
    );
  }

  Widget _buildMetricCard(String label, String value) {
    final isGrowth = label == 'Growth' || label == 'vs Last';
    final isNegative = value.startsWith('-');

    return Expanded(
      child: Card(
        margin: EdgeInsets.zero,
        child: Padding(
          padding: const EdgeInsets.all(8),
          child: Column(
            children: [
              Text(
                value,
                style: AppTextStyles.titleMedium.copyWith(
                  color: isGrowth
                      ? (isNegative ? AppColors.error : AppColors.success)
                      : AppColors.textPrimary,
                ),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
              const SizedBox(height: 2),
              Text(label, style: AppTextStyles.caption),
            ],
          ),
        ),
      ),
    );
  }

  List<Widget> _buildMonthlyList(List<Map<String, dynamic>> trends) {
    if (trends.isEmpty) {
      return [
        Center(
          child: Padding(
            padding: const EdgeInsets.all(32),
            child: Text('No data available', style: AppTextStyles.bodySmall),
          ),
        ),
      ];
    }

    return trends.reversed.map((item) {
      final period = item['period'] ?? item['month'] ?? '';
      final revenue = (item['revenue'] ?? 0).toDouble();
      final profit = (item['profit'] ?? 0).toDouble();
      final orders = item['orders'] ?? 0;
      final growth = (item['growth'] ?? 0).toDouble();

      return Card(
        margin: const EdgeInsets.only(bottom: 8),
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Row(
            children: [
              Expanded(
                flex: 2,
                child: Text(
                  period.toString(),
                  style: AppTextStyles.bodyMedium,
                ),
              ),
              Expanded(
                flex: 3,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '\$${_formatValue(revenue)}',
                      style: AppTextStyles.titleMedium,
                    ),
                    Text(
                      '$orders orders',
                      style: AppTextStyles.caption,
                    ),
                  ],
                ),
              ),
              Expanded(
                flex: 2,
                child: TrendIndicator(percentage: growth),
              ),
            ],
          ),
        ),
      );
    }).toList();
  }

  String _formatValue(double val) {
    if (val >= 1000000) {
      return '${(val / 1000000).toStringAsFixed(1)}M';
    } else if (val >= 1000) {
      return '${(val / 1000).toStringAsFixed(1)}K';
    }
    return val.toStringAsFixed(0);
  }
}
