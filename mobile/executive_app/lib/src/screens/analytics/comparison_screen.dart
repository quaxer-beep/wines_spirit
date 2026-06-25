import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shared_core/shared_core.dart';
import '../../providers/branch_provider.dart';
import '../../widgets/comparison_bar.dart';

class ComparisonScreen extends StatefulWidget {
  const ComparisonScreen({super.key});

  @override
  State<ComparisonScreen> createState() => _ComparisonScreenState();
}

class _ComparisonScreenState extends State<ComparisonScreen> {
  final List<Map<String, String>> _metrics = [
    {'key': 'revenue', 'label': 'Revenue'},
    {'key': 'profit', 'label': 'Profit'},
    {'key': 'expenses', 'label': 'Expenses'},
    {'key': 'inventory_value', 'label': 'Inventory'},
    {'key': 'staff_count', 'label': 'Staff Count'},
  ];

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<BranchProvider>().fetchBranchComparisons();
    });
  }

  @override
  Widget build(BuildContext context) {
    final branchProvider = context.watch<BranchProvider>();
    final selectedMetric = branchProvider.selectedMetric ?? 'revenue';

    return Scaffold(
      appBar: AppBar(
        title: const Text('Branch Comparison'),
      ),
      body: Column(
        children: [
          Container(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Compare by:', style: AppTextStyles.titleMedium),
                const SizedBox(height: 8),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: _metrics.map((metric) {
                    final isSelected = selectedMetric == metric['key'];
                    return ChoiceChip(
                      label: Text(metric['label']!),
                      selected: isSelected,
                      onSelected: (_) {
                        branchProvider.compareByMetric(metric['key']!);
                      },
                      selectedColor: AppColors.primary,
                      labelStyle: TextStyle(
                        color: isSelected ? Colors.white : AppColors.textPrimary,
                      ),
                    );
                  }).toList(),
                ),
              ],
            ),
          ),
          if (branchProvider.isLoading)
            const Expanded(
              child: Center(child: CircularProgressIndicator()),
            )
          else if (branchProvider.branchComparisons.isEmpty)
            const Expanded(
              child: Center(child: Text('No branch data available')),
            )
          else
            Expanded(
              child: ListView.builder(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                itemCount: branchProvider.branchComparisons.length,
                itemBuilder: (context, index) {
                  final branch = branchProvider.branchComparisons[index];
                  final isBest = index == 0;
                  return _buildBranchCard(branch, selectedMetric, isBest);
                },
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildBranchCard(
    Map<String, dynamic> branch,
    String metric,
    bool isBest,
  ) {
    final name = branch['name'] ?? '';
    final revenue = (branch['revenue'] ?? 0).toDouble();
    final profit = (branch['profit'] ?? 0).toDouble();
    final expenses = (branch['expenses'] ?? 0).toDouble();
    final inventoryValue = (branch['inventory_value'] ?? 0).toDouble();
    final staffCount = branch['staff_count'] ?? 0;

    final allValues = context
        .read<BranchProvider>()
        .branchComparisons
        .map((b) => (b[metric] ?? 0).toDouble())
        .toList();
    final maxValue = allValues.isEmpty ? 0.0 : allValues.reduce((a, b) => a > b ? a : b);
    final metricValue = (branch[metric] ?? 0).toDouble();

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: isBest
            ? const BorderSide(color: AppColors.loyaltyGold, width: 2)
            : BorderSide.none,
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                if (isBest)
                  const Padding(
                    padding: EdgeInsets.only(right: 8),
                    child: Icon(
                      Icons.emoji_events,
                      color: AppColors.loyaltyGold,
                      size: 20,
                    ),
                  ),
                Expanded(
                  child: Text(
                    name,
                    style: AppTextStyles.titleLarge.copyWith(
                      color: isBest ? AppColors.loyaltyGold : AppColors.textPrimary,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            ComparisonBar(
              label: 'Revenue',
              value: revenue,
              maxValue: maxValue,
              color: AppColors.success,
            ),
            ComparisonBar(
              label: 'Profit',
              value: profit,
              maxValue: maxValue,
              color: AppColors.primary,
            ),
            ComparisonBar(
              label: 'Expenses',
              value: expenses,
              maxValue: maxValue,
              color: AppColors.warning,
            ),
            ComparisonBar(
              label: 'Inventory',
              value: inventoryValue,
              maxValue: maxValue,
              color: AppColors.info,
            ),
            ComparisonBar(
              label: 'Staff',
              value: staffCount.toDouble(),
              maxValue: maxValue,
              color: const Color(0xFF7B1FA2),
            ),
          ],
        ),
      ),
    );
  }
}
