import 'package:flutter/material.dart';
import 'package:shared_core/shared_core.dart';

class BranchDetailScreen extends StatelessWidget {
  final Map<String, dynamic> branch;

  const BranchDetailScreen({super.key, required this.branch});

  @override
  Widget build(BuildContext context) {
    final name = branch['name'] ?? '';
    final location = branch['location'] ?? '';
    final contactEmail = branch['contact_email'] ?? '';
    final contactPhone = branch['contact_phone'] ?? '';
    final todaySales = (branch['today_sales'] ?? 0).toDouble();
    final orders = branch['order_count'] ?? 0;
    final staffCount = branch['staff_count'] ?? 0;
    final transfers = List<Map<String, dynamic>>.from(branch['transfers'] ?? []);

    return Scaffold(
      appBar: AppBar(
        title: Text(name),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Card(
              margin: EdgeInsets.zero,
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        const Icon(Icons.store, color: AppColors.primary),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            name,
                            style: AppTextStyles.headlineMedium,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    if (location.isNotEmpty)
                      _infoRow(Icons.location_on, location),
                    if (contactEmail.isNotEmpty)
                      _infoRow(Icons.email, contactEmail),
                    if (contactPhone.isNotEmpty)
                      _infoRow(Icons.phone, contactPhone),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                _buildKpiSmall('Today Sales', '\$${_formatValue(todaySales)}'),
                const SizedBox(width: 8),
                _buildKpiSmall('Orders', orders.toString()),
                const SizedBox(width: 8),
                _buildKpiSmall('Staff', staffCount.toString()),
              ],
            ),
            const SizedBox(height: 16),
            Card(
              margin: EdgeInsets.zero,
              child: Container(
                height: 200,
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Sales Trend', style: AppTextStyles.titleLarge),
                    const Spacer(),
                    Center(
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          const Icon(
                            Icons.show_chart,
                            size: 48,
                            color: AppColors.textHint,
                          ),
                          const SizedBox(height: 8),
                          Text(
                            'Chart placeholder',
                            style: AppTextStyles.bodySmall,
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),
            Text('Staff Summary', style: AppTextStyles.titleLarge),
            const SizedBox(height: 8),
            Card(
              margin: EdgeInsets.zero,
              child: ListTile(
                leading: const Icon(Icons.people, color: AppColors.primary),
                title: Text('$staffCount staff members'),
                subtitle: const Text('View details'),
                trailing: const Icon(Icons.chevron_right),
                onTap: () {},
              ),
            ),
            const SizedBox(height: 16),
            Text('Transfer History', style: AppTextStyles.titleLarge),
            const SizedBox(height: 8),
            if (transfers.isEmpty)
              Card(
                margin: EdgeInsets.zero,
                child: Padding(
                  padding: const EdgeInsets.all(32),
                  child: Center(
                    child: Text(
                      'No transfers',
                      style: AppTextStyles.bodySmall,
                    ),
                  ),
                ),
              )
            else
              ...transfers.take(5).map((t) => Card(
                    margin: const EdgeInsets.only(bottom: 8),
                    child: ListTile(
                      title: Text(t['reference'] ?? ''),
                      subtitle: Text(
                        '\$${_formatValue((t['value'] ?? 0).toDouble())}',
                      ),
                      trailing: Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 8,
                          vertical: 2,
                        ),
                        decoration: BoxDecoration(
                          color: AppColors.statusColor(
                            t['status'] ?? '',
                          ).withOpacity(0.1),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Text(
                          (t['status'] ?? '').toString().toUpperCase(),
                          style: AppTextStyles.caption.copyWith(
                            color: AppColors.statusColor(t['status'] ?? ''),
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                    ),
                  )),
            const SizedBox(height: 24),
            Text('Quick Actions', style: AppTextStyles.titleLarge),
            const SizedBox(height: 8),
            Card(
              margin: EdgeInsets.zero,
              child: Column(
                children: [
                  ListTile(
                    leading: const Icon(Icons.people, color: AppColors.primary),
                    title: const Text('View Staff'),
                    trailing: const Icon(Icons.chevron_right),
                    onTap: () {},
                  ),
                  const Divider(height: 1),
                  ListTile(
                    leading: const Icon(Icons.inventory, color: AppColors.primary),
                    title: const Text('Stock Report'),
                    trailing: const Icon(Icons.chevron_right),
                    onTap: () {},
                  ),
                  const Divider(height: 1),
                  ListTile(
                    leading: const Icon(Icons.assessment, color: AppColors.primary),
                    title: const Text('Sales Report'),
                    trailing: const Icon(Icons.chevron_right),
                    onTap: () {},
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _infoRow(IconData icon, String text) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 4),
      child: Row(
        children: [
          Icon(icon, size: 16, color: AppColors.textSecondary),
          const SizedBox(width: 8),
          Expanded(
            child: Text(text, style: AppTextStyles.bodyMedium),
          ),
        ],
      ),
    );
  }

  Widget _buildKpiSmall(String label, String value) {
    return Expanded(
      child: Card(
        margin: EdgeInsets.zero,
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Column(
            children: [
              Text(
                value,
                style: AppTextStyles.headlineSmall.copyWith(
                  color: AppColors.primary,
                ),
              ),
              const SizedBox(height: 4),
              Text(label, style: AppTextStyles.caption),
            ],
          ),
        ),
      ),
    );
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
