import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shared_core/shared_core.dart';
import '../../providers/expense_provider.dart';

class ExpenseListScreen extends StatefulWidget {
  const ExpenseListScreen({super.key});

  @override
  State<ExpenseListScreen> createState() => _ExpenseListScreenState();
}

class _ExpenseListScreenState extends State<ExpenseListScreen> {
  int _selectedMonth = DateTime.now().month;
  int _selectedYear = DateTime.now().year;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<ExpenseProvider>().fetchExpenses();
    });
  }

  List<Map<String, dynamic>> _filteredExpenses(ExpenseProvider provider) {
    return provider.expenses.where((e) {
      final dateStr = e['date'] as String?;
      if (dateStr == null) return true;
      try {
        final date = DateTime.parse(dateStr);
        return date.month == _selectedMonth && date.year == _selectedYear;
      } catch (_) {
        return true;
      }
    }).toList();
  }

  Map<String, double> _categoryBreakdown(List<Map<String, dynamic>> expenses) {
    final map = <String, double>{};
    for (final e in expenses) {
      final cat = e['category'] as String? ?? 'Other';
      final amount = (e['amount'] as num?)?.toDouble() ?? 0;
      map[cat] = (map[cat] ?? 0) + amount;
    }
    return map;
  }

  static const _categoryColors = {
    'Utilities': Color(0xFF1976D2),
    'Rent': Color(0xFF7B1FA2),
    'Salaries': Color(0xFF2E7D32),
    'Supplies': Color(0xFFF57C00),
    'Marketing': Color(0xFFC62828),
    'Maintenance': Color(0xFF00838F),
    'Other': Color(0xFF6D4C41),
  };

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Expenses')),
      body: Consumer<ExpenseProvider>(
        builder: (context, provider, _) {
          if (provider.isLoading && provider.expenses.isEmpty) {
            return const ShimmerLoading(itemCount: 5, itemBuilder: _shimmerItem);
          }
          if (provider.error != null && provider.expenses.isEmpty) {
            return ErrorDisplay(
              message: provider.error!,
              onRetry: () => provider.fetchExpenses(),
            );
          }
          final filtered = _filteredExpenses(provider);
          final breakdown = _categoryBreakdown(filtered);
          final total = filtered.fold<double>(
              0, (sum, e) => sum + ((e['amount'] as num?)?.toDouble() ?? 0));

          return RefreshIndicator(
            onRefresh: () => provider.fetchExpenses(),
            child: SingleChildScrollView(
              physics: const AlwaysScrollableScrollPhysics(),
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: DropdownButtonFormField<int>(
                          value: _selectedMonth,
                          decoration: const InputDecoration(
                            labelText: 'Month',
                            contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                          ),
                          items: List.generate(12, (i) {
                            return DropdownMenuItem(
                              value: i + 1,
                              child: Text(DateFormat('MMMM').format(DateTime(2000, i + 1))),
                            );
                          }),
                          onChanged: (v) => setState(() => _selectedMonth = v ?? DateTime.now().month),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: DropdownButtonFormField<int>(
                          value: _selectedYear,
                          decoration: const InputDecoration(
                            labelText: 'Year',
                            contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                          ),
                          items: List.generate(5, (i) {
                            final year = DateTime.now().year - 2 + i;
                            return DropdownMenuItem(value: year, child: Text('$year'));
                          }),
                          onChanged: (v) => setState(() => _selectedYear = v ?? DateTime.now().year),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('Total Expenses', style: AppTextStyles.bodySmall),
                          const SizedBox(height: 8),
                          Text(
                            'KSh ${total.toStringAsFixed(0)}',
                            style: AppTextStyles.displaySmall.copyWith(
                              color: AppColors.error,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),
                  Text('Category Breakdown', style: AppTextStyles.titleLarge),
                  const SizedBox(height: 8),
                  if (breakdown.isEmpty)
                    const Card(
                      child: Padding(
                        padding: EdgeInsets.all(24),
                        child: Center(
                          child: Text('No expenses', style: AppTextStyles.bodySmall),
                        ),
                      ),
                    )
                  else
                    Card(
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          children: [
                            Container(
                              height: 160,
                              child: Row(
                                children: breakdown.entries.map((e) {
                                  final ratio = total > 0 ? e.value / total : 0;
                                  final color = _categoryColors[e.key] ?? Colors.grey;
                                  return Expanded(
                                    flex: (ratio * 100).round().clamp(1, 100),
                                    child: Container(
                                      margin: const EdgeInsets.symmetric(horizontal: 1),
                                      decoration: BoxDecoration(
                                        color: color,
                                        borderRadius: BorderRadius.circular(4),
                                      ),
                                    ),
                                  );
                                }).toList(),
                              ),
                            ),
                            const SizedBox(height: 12),
                            ...breakdown.entries.map((e) {
                              final color = _categoryColors[e.key] ?? Colors.grey;
                              return Padding(
                                padding: const EdgeInsets.symmetric(vertical: 2),
                                child: Row(
                                  children: [
                                    Container(
                                      width: 12,
                                      height: 12,
                                      decoration: BoxDecoration(
                                        color: color,
                                        borderRadius: BorderRadius.circular(2),
                                      ),
                                    ),
                                    const SizedBox(width: 8),
                                    Expanded(child: Text(e.key, style: AppTextStyles.bodyMedium)),
                                    Text(
                                      Formatters.formatCurrency(e.value),
                                      style: AppTextStyles.priceSmall,
                                    ),
                                  ],
                                ),
                              );
                            }),
                          ],
                        ),
                      ),
                    ),
                  const SizedBox(height: 24),
                  Text('Expense List', style: AppTextStyles.titleLarge),
                  const SizedBox(height: 8),
                  if (filtered.isEmpty)
                    const Card(
                      child: Padding(
                        padding: EdgeInsets.all(24),
                        child: Center(
                          child: Text('No expenses found', style: AppTextStyles.bodySmall),
                        ),
                      ),
                    )
                  else
                    ...filtered.map((e) {
                      final cat = e['category'] as String? ?? 'Other';
                      final color = _categoryColors[cat] ?? Colors.grey;
                      final desc = e['description'] as String? ?? '';
                      final amount = (e['amount'] as num?)?.toDouble() ?? 0;
                      final date = e['date'] as String? ?? '';
                      final id = e['id'] as int? ?? 0;
                      IconData icon;
                      switch (cat.toLowerCase()) {
                        case 'utilities':
                          icon = Icons.lightbulb;
                          break;
                        case 'rent':
                          icon = Icons.home;
                          break;
                        case 'salaries':
                          icon = Icons.people;
                          break;
                        case 'supplies':
                          icon = Icons.inventory;
                          break;
                        case 'marketing':
                          icon = Icons.campaign;
                          break;
                        case 'maintenance':
                          icon = Icons.build;
                          break;
                        default:
                          icon = Icons.receipt;
                      }
                      return Card(
                        margin: const EdgeInsets.only(bottom: 4),
                        child: ListTile(
                          leading: CircleAvatar(
                            backgroundColor: color.withValues(alpha: 0.15),
                            child: Icon(icon, color: color, size: 20),
                          ),
                          title: Text(desc, style: AppTextStyles.titleMedium),
                          subtitle: Text(Formatters.formatDate(date), style: AppTextStyles.caption),
                          trailing: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Text(
                                Formatters.formatCurrency(amount),
                                style: AppTextStyles.priceSmall,
                              ),
                              const SizedBox(width: 8),
                              IconButton(
                                icon: const Icon(Icons.delete_outline, size: 20, color: AppColors.error),
                                onPressed: () {
                                  showDialog(
                                    context: context,
                                    builder: (ctx) => AlertDialog(
                                      title: const Text('Delete Expense'),
                                      content: const Text('Are you sure?'),
                                      actions: [
                                        TextButton(
                                          onPressed: () => Navigator.pop(ctx),
                                          child: const Text('Cancel'),
                                        ),
                                        ElevatedButton(
                                          onPressed: () {
                                            provider.deleteExpense(id);
                                            Navigator.pop(ctx);
                                          },
                                          style: ElevatedButton.styleFrom(
                                            backgroundColor: AppColors.error,
                                          ),
                                          child: const Text('Delete'),
                                        ),
                                      ],
                                    ),
                                  );
                                },
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
      floatingActionButton: FloatingActionButton(
        onPressed: () => Navigator.of(context).pushNamed('/expense-add'),
        child: const Icon(Icons.add),
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
