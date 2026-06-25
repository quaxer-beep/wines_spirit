import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shared_core/shared_core.dart';
import '../../providers/manager_auth_provider.dart';
import '../../providers/manager_dashboard_provider.dart';
import '../../widgets/kpi_card.dart';
import '../../widgets/stock_alert_card.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<ManagerDashboardProvider>().fetchDashboard();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Manager Dashboard'),
        actions: [
          IconButton(
            icon: const Icon(Icons.notifications_outlined),
            onPressed: () {},
          ),
          Consumer<ManagerAuthProvider>(
            builder: (context, auth, _) {
              return PopupMenuButton<String>(
                icon: CircleAvatar(
                  radius: 16,
                  backgroundColor: AppColors.primaryLight,
                  child: Text(
                    auth.user?['full_name']?.toString().isNotEmpty == true
                        ? '${(auth.user!['full_name'] as String).split(' ').first[0]}${(auth.user!['full_name'] as String).split(' ').length > 1 ? (auth.user!['full_name'] as String).split(' ')[1][0] : ''}'
                        : 'M',
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
                onSelected: (value) {
                  if (value == 'logout') {
                    auth.logout();
                    Navigator.of(context).pushReplacementNamed('/login');
                  } else if (value == 'profile') {
                    Navigator.of(context).pushNamed('/profile');
                  }
                },
                itemBuilder: (_) => [
                  const PopupMenuItem(value: 'profile', child: Text('Profile')),
                  const PopupMenuItem(value: 'logout', child: Text('Logout')),
                ],
              );
            },
          ),
        ],
      ),
      body: Consumer<ManagerDashboardProvider>(
        builder: (context, dashboard, _) {
          if (dashboard.isLoading) {
            return const ShimmerLoading(itemCount: 6, itemBuilder: _shimmerItem);
          }
          if (dashboard.error != null) {
            return ErrorDisplay(
              message: dashboard.error!,
              onRetry: () => dashboard.fetchDashboard(),
            );
          }
          return RefreshIndicator(
            onRefresh: () => dashboard.fetchDashboard(),
            child: SingleChildScrollView(
              physics: const AlwaysScrollableScrollPhysics(),
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _buildBranchInfo(),
                  const SizedBox(height: 16),
                  _buildKpiGrid(dashboard),
                  const SizedBox(height: 24),
                  Text('Quick Actions', style: AppTextStyles.titleLarge),
                  const SizedBox(height: 12),
                  _buildQuickActions(),
                  const SizedBox(height: 24),
                  if (dashboard.lowStockItems > 0) ...[
                    Row(
                      children: [
                        Text('Low Stock Alerts', style: AppTextStyles.titleLarge),
                        const SizedBox(width: 8),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                          decoration: BoxDecoration(
                            color: AppColors.error,
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Text(
                            '${dashboard.lowStockItems}',
                            style: const TextStyle(
                              color: Colors.white,
                              fontSize: 12,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    const StockAlertCard(
                      productName: 'View all low stock items',
                      currentStock: 0,
                      reorderLevel: 0,
                      category: 'Tap to view',
                    ),
                  ],
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _buildBranchInfo() {
    return Consumer<ManagerAuthProvider>(
      builder: (context, auth, _) {
        if (auth.branchName == null) return const SizedBox.shrink();
        return Card(
          child: ListTile(
            leading: const Icon(Icons.store, color: AppColors.primary),
            title: Text(auth.branchName!, style: AppTextStyles.titleMedium),
            subtitle: Text('Branch ID: ${auth.branchId}', style: AppTextStyles.caption),
          ),
        );
      },
    );
  }

  Widget _buildKpiGrid(ManagerDashboardProvider dashboard) {
    return GridView.count(
      crossAxisCount: 2,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      mainAxisSpacing: 12,
      crossAxisSpacing: 12,
      childAspectRatio: 1.3,
      children: [
        KpiCard(
          title: "Today's Sales",
          value: 'KSh ${dashboard.todaySales.toStringAsFixed(0)}',
          icon: Icons.trending_up,
          accentColor: AppColors.success,
        ),
        KpiCard(
          title: 'Orders Today',
          value: '${dashboard.todayOrders}',
          icon: Icons.receipt_long,
          accentColor: AppColors.primary,
        ),
        KpiCard(
          title: 'Low Stock Items',
          value: '${dashboard.lowStockItems}',
          icon: Icons.inventory,
          accentColor: dashboard.lowStockItems > 0
              ? AppColors.error
              : AppColors.success,
        ),
        KpiCard(
          title: 'Pending Approvals',
          value: '${dashboard.pendingApprovals}',
          icon: Icons.approval,
          accentColor: dashboard.pendingApprovals > 0
              ? AppColors.warning
              : AppColors.success,
        ),
      ],
    );
  }

  Widget _buildQuickActions() {
    final actions = [
      {'icon': Icons.inventory, 'label': 'View Inventory', 'route': '/inventory'},
      {'icon': Icons.bar_chart, 'label': 'Sales Report', 'route': '/sales'},
      {'icon': Icons.account_balance_wallet, 'label': 'Expenses', 'route': '/expenses'},
      {'icon': Icons.approval, 'label': 'Approvals', 'route': '/approvals'},
    ];
    return GridView.count(
      crossAxisCount: 2,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      mainAxisSpacing: 12,
      crossAxisSpacing: 12,
      childAspectRatio: 1.5,
      children: actions.map((a) {
        return Card(
          child: InkWell(
            onTap: () => Navigator.of(context).pushNamed(a['route'] as String),
            borderRadius: BorderRadius.circular(12),
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Icon(a['icon'] as IconData, color: AppColors.primary),
                      const Icon(Icons.chevron_right, color: AppColors.textHint),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(a['label'] as String, style: AppTextStyles.titleMedium),
                ],
              ),
            ),
          ),
        );
      }).toList(),
    );
  }

  static Widget _shimmerItem(int index) {
    return Card(
      child: Container(
        height: 100,
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(height: 12, width: 80, color: Colors.grey[300]),
            const SizedBox(height: 8),
            Container(height: 20, width: 120, color: Colors.grey[300]),
          ],
        ),
      ),
    );
  }
}
