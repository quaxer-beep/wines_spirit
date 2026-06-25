import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shared_core/shared_core.dart';
import '../../providers/sales_provider.dart';

class SalesScreen extends StatefulWidget {
  const SalesScreen({super.key});

  @override
  State<SalesScreen> createState() => _SalesScreenState();
}

class _SalesScreenState extends State<SalesScreen> {
  DateTimeRange? _dateRange;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<SalesProvider>().fetchSales();
    });
  }

  Future<void> _pickDateRange() async {
    final picked = await showDateRangePicker(
      context: context,
      firstDate: DateTime(2020),
      lastDate: DateTime.now(),
      initialDateRange: _dateRange ?? DateTimeRange(
        start: DateTime.now().subtract(const Duration(days: 7)),
        end: DateTime.now(),
      ),
    );
    if (picked != null) {
      setState(() => _dateRange = picked);
      if (!mounted) return;
      context.read<SalesProvider>().fetchSalesByDateRange(picked.start, picked.end);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Sales Report'),
        actions: [
          IconButton(
            icon: const Icon(Icons.date_range),
            onPressed: _pickDateRange,
          ),
        ],
      ),
      body: Consumer<SalesProvider>(
        builder: (context, sales, _) {
          if (sales.isLoading) {
            return const ShimmerLoading(itemCount: 5, itemBuilder: _shimmerItem);
          }
          if (sales.error != null) {
            return ErrorDisplay(
              message: sales.error!,
              onRetry: () => sales.fetchSales(),
            );
          }
          return RefreshIndicator(
            onRefresh: () => sales.fetchSales(),
            child: SingleChildScrollView(
              physics: const AlwaysScrollableScrollPhysics(),
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (_dateRange != null)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 16),
                      child: Text(
                        '${Formatters.formatDate(_dateRange!.start.toIso8601String())} - ${Formatters.formatDate(_dateRange!.end.toIso8601String())}',
                        style: AppTextStyles.bodySmall,
                      ),
                    ),
                  Row(
                    children: [
                      Expanded(
                        child: Card(
                          child: Padding(
                            padding: const EdgeInsets.all(16),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text('Total Revenue', style: AppTextStyles.bodySmall),
                                const SizedBox(height: 8),
                                Text(
                                  'KSh ${sales.totalRevenue.toStringAsFixed(0)}',
                                  style: AppTextStyles.displaySmall.copyWith(
                                    color: AppColors.success,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Card(
                          child: Padding(
                            padding: const EdgeInsets.all(16),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text('Transactions', style: AppTextStyles.bodySmall),
                                const SizedBox(height: 8),
                                Text(
                                  '${sales.transactionCount}',
                                  style: AppTextStyles.displaySmall,
                                ),
                              ],
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 24),
                  Text('Top Selling Products', style: AppTextStyles.titleLarge),
                  const SizedBox(height: 8),
                  if (sales.topProducts.isEmpty)
                    const Card(
                      child: Padding(
                        padding: EdgeInsets.all(24),
                        child: Center(child: Text('No data', style: AppTextStyles.bodySmall)),
                      ),
                    )
                  else
                    ...sales.topProducts.asMap().entries.map((entry) {
                      final i = entry.key + 1;
                      final p = entry.value;
                      return Card(
                        margin: const EdgeInsets.only(bottom: 4),
                        child: ListTile(
                          leading: CircleAvatar(
                            backgroundColor: AppColors.primary,
                            child: Text('$i',
                                style: const TextStyle(color: Colors.white)),
                          ),
                          title: Text(p['name'] as String? ?? '',
                              style: AppTextStyles.titleMedium),
                          subtitle: Text(
                            '${p['quantity_sold'] ?? 0} sold',
                            style: AppTextStyles.caption,
                          ),
                          trailing: Text(
                            Formatters.formatCurrency(
                                (p['revenue'] as num?)?.toDouble() ?? 0),
                            style: AppTextStyles.priceSmall,
                          ),
                        ),
                      );
                    }),
                  const SizedBox(height: 24),
                  Text('Recent Transactions', style: AppTextStyles.titleLarge),
                  const SizedBox(height: 8),
                  if (sales.todaySales.isEmpty)
                    const Card(
                      child: Padding(
                        padding: EdgeInsets.all(24),
                        child: Center(child: Text('No transactions', style: AppTextStyles.bodySmall)),
                      ),
                    )
                  else
                    ...sales.todaySales.map((t) {
                      return Card(
                        margin: const EdgeInsets.only(bottom: 4),
                        child: ListTile(
                          leading: CircleAvatar(
                            backgroundColor: AppColors.surfaceVariant,
                            child: const Icon(Icons.receipt, color: AppColors.primary),
                          ),
                          title: Text(
                            'Order #${t['id'] ?? ''}',
                            style: AppTextStyles.titleMedium,
                          ),
                          subtitle: Text(
                            '${t['customer_name'] ?? 'Walk-in'} • ${Formatters.formatTime(t['created_at'] as String?)}',
                            style: AppTextStyles.caption,
                          ),
                          trailing: Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            crossAxisAlignment: CrossAxisAlignment.end,
                            children: [
                              Text(
                                Formatters.formatCurrency(
                                    (t['total_amount'] as num?)?.toDouble() ?? 0),
                                style: AppTextStyles.priceSmall,
                              ),
                              Text(
                                t['status'] as String? ?? '',
                                style: AppTextStyles.caption.copyWith(
                                  color: AppColors.statusColor(t['status'] as String? ?? ''),
                                ),
                              ),
                            ],
                          ),
                        ),
                      );
                    }),
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  static Widget _shimmerItem(int index) {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      child: Container(
        height: 60,
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(height: 12, width: 120, color: Colors.grey[300]),
            const SizedBox(height: 6),
            Container(height: 10, width: 80, color: Colors.grey[300]),
          ],
        ),
      ),
    );
  }
}
