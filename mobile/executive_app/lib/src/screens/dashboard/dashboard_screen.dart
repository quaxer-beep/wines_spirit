import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shared_core/shared_core.dart';
import '../../providers/exec_dashboard_provider.dart';
import '../../widgets/kpi_card.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  String _selectedPeriod = 'today';

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<ExecDashboardProvider>().fetchDashboard(_selectedPeriod);
    });
  }

  Future<void> _onRefresh() async {
    await context.read<ExecDashboardProvider>().fetchDashboard(_selectedPeriod);
  }

  @override
  Widget build(BuildContext context) {
    final dashboard = context.watch<ExecDashboardProvider>();

    return Scaffold(
      appBar: AppBar(
        title: const Text('Executive Dashboard'),
        actions: [
          PopupMenuButton<String>(
            icon: const Icon(Icons.calendar_today),
            onSelected: (period) {
              setState(() => _selectedPeriod = period);
              dashboard.fetchDashboard(period);
            },
            itemBuilder: (_) => [
              const PopupMenuItem(value: 'today', child: Text('Today')),
              const PopupMenuItem(value: 'week', child: Text('This Week')),
              const PopupMenuItem(value: 'month', child: Text('This Month')),
              const PopupMenuItem(value: 'quarter', child: Text('This Quarter')),
              const PopupMenuItem(value: 'year', child: Text('This Year')),
            ],
          ),
        ],
      ),
      body: dashboard.isLoading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _onRefresh,
              child: ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  GridView.count(
                    crossAxisCount: 2,
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    mainAxisSpacing: 12,
                    crossAxisSpacing: 12,
                    childAspectRatio: 1.1,
                    children: [
                      KpiCard(
                        label: 'Total Revenue',
                        value: '\$${_formatValue(dashboard.totalRevenue)}',
                        growthPercentage: dashboard.revenueGrowth,
                        leading: Icon(
                          Icons.trending_up,
                          color: dashboard.revenueGrowth >= 0
                              ? AppColors.success
                              : AppColors.error,
                        ),
                      ),
                      KpiCard(
                        label: 'Net Profit',
                        value: '\$${_formatValue(dashboard.totalProfit)}',
                        growthPercentage: dashboard.profitGrowth,
                        leading: Icon(
                          Icons.account_balance,
                          color: dashboard.profitGrowth >= 0
                              ? AppColors.success
                              : AppColors.error,
                        ),
                      ),
                      KpiCard(
                        label: 'Inventory Value',
                        value: '\$${_formatValue(dashboard.totalInventoryValue)}',
                        leading: const Icon(
                          Icons.inventory_2,
                          color: AppColors.info,
                        ),
                      ),
                      KpiCard(
                        label: 'Total Branches',
                        value: dashboard.totalBranches.toString(),
                        subtitle: '${dashboard.totalOrders} orders',
                        leading: const Icon(
                          Icons.store,
                          color: AppColors.loyaltyGold,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 24),
                  Card(
                    margin: EdgeInsets.zero,
                    child: Container(
                      height: 200,
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Revenue Trend',
                            style: AppTextStyles.titleLarge,
                          ),
                          const Spacer(),
                          Center(
                            child: Column(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                Icon(
                                  Icons.show_chart,
                                  size: 64,
                                  color: AppColors.textHint,
                                ),
                                const SizedBox(height: 8),
                                Text(
                                  'Chart loading...',
                                  style: AppTextStyles.bodySmall,
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 24),
                  Text(
                    'Quick Links',
                    style: AppTextStyles.titleLarge,
                  ),
                  const SizedBox(height: 8),
                  Card(
                    margin: EdgeInsets.zero,
                    child: Column(
                      children: [
                        ListTile(
                          leading: const Icon(
                            Icons.analytics,
                            color: AppColors.primary,
                          ),
                          title: const Text('Analytics'),
                          subtitle: const Text('Revenue by branch, brand, category'),
                          trailing: const Icon(Icons.chevron_right),
                          onTap: () => Navigator.pushNamed(context, '/analytics'),
                        ),
                        const Divider(height: 1),
                        ListTile(
                          leading: const Icon(
                            Icons.store,
                            color: AppColors.primary,
                          ),
                          title: const Text('Branches'),
                          subtitle: const Text('Compare branch performance'),
                          trailing: const Icon(Icons.chevron_right),
                          onTap: () => Navigator.pushNamed(context, '/branches'),
                        ),
                        const Divider(height: 1),
                        ListTile(
                          leading: const Icon(
                            Icons.swap_horiz,
                            color: AppColors.primary,
                          ),
                          title: const Text('Transfers'),
                          subtitle: const Text('Stock transfers between branches'),
                          trailing: const Icon(Icons.chevron_right),
                          onTap: () => Navigator.pushNamed(context, '/transfers'),
                        ),
                      ],
                    ),
                  ),
                ],
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
