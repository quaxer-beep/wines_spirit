import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shared_core/shared_core.dart';
import '../../providers/exec_auth_provider.dart';
import '../../widgets/trend_indicator.dart';

class BranchListScreen extends StatefulWidget {
  const BranchListScreen({super.key});

  @override
  State<BranchListScreen> createState() => _BranchListScreenState();
}

class _BranchListScreenState extends State<BranchListScreen> {
  String _searchQuery = '';
  bool _showTodayRevenue = true;

  @override
  Widget build(BuildContext context) {
    final authProvider = context.watch<ExecAuthProvider>();
    final branches = authProvider.accessibleBranches;

    final filteredBranches = branches.where((b) {
      if (_searchQuery.isEmpty) return true;
      final name = (b['name'] ?? '').toString().toLowerCase();
      final location = (b['location'] ?? '').toString().toLowerCase();
      final query = _searchQuery.toLowerCase();
      return name.contains(query) || location.contains(query);
    }).toList();

    return Scaffold(
      appBar: AppBar(
        title: const Text('Branches'),
        actions: [
          IconButton(
            icon: Icon(
              _showTodayRevenue ? Icons.today : Icons.date_range,
            ),
            onPressed: () {
              setState(() => _showTodayRevenue = !_showTodayRevenue);
            },
            tooltip: _showTodayRevenue ? 'Today\'s revenue' : 'Total revenue',
          ),
        ],
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(16),
            child: TextField(
              onChanged: (value) => setState(() => _searchQuery = value),
              decoration: InputDecoration(
                hintText: 'Search branches...',
                prefixIcon: const Icon(Icons.search),
                filled: true,
                fillColor: AppColors.surfaceVariant,
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                  borderSide: BorderSide.none,
                ),
                contentPadding: const EdgeInsets.symmetric(vertical: 12),
              ),
            ),
          ),
          Expanded(
            child: filteredBranches.isEmpty
                ? const Center(child: Text('No branches found'))
                : ListView.builder(
                    itemCount: filteredBranches.length,
                    itemBuilder: (context, index) {
                      final branch = filteredBranches[index];
                      return _buildBranchItem(branch);
                    },
                  ),
          ),
        ],
      ),
    );
  }

  Widget _buildBranchItem(Map<String, dynamic> branch) {
    final name = branch['name'] ?? '';
    final location = branch['location'] ?? '';
    final revenue = _showTodayRevenue
        ? (branch['today_revenue'] ?? 0).toDouble()
        : (branch['total_revenue'] ?? 0).toDouble();
    final performance = (branch['performance'] ?? 0).toDouble();
    final orderCount = branch['order_count'] ?? 0;
    final isActive = branch['status']?.toString().toLowerCase() != 'inactive';

    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        leading: CircleAvatar(
          backgroundColor: isActive
              ? AppColors.primary.withOpacity(0.1)
              : AppColors.textHint.withOpacity(0.1),
          child: Icon(
            Icons.store,
            color: isActive ? AppColors.primary : AppColors.textHint,
          ),
        ),
        title: Text(
          name,
          style: AppTextStyles.titleMedium,
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const SizedBox(height: 4),
            Text(
              location,
              style: AppTextStyles.bodySmall,
            ),
            const SizedBox(height: 4),
            Row(
              children: [
                Text(
                  '\$${_formatValue(revenue)}',
                  style: AppTextStyles.bodyMedium.copyWith(
                    fontWeight: FontWeight.w600,
                    color: AppColors.primary,
                  ),
                ),
                const SizedBox(width: 8),
                TrendIndicator(
                  percentage: performance,
                  size: TrendIndicatorSize.small,
                ),
                const SizedBox(width: 12),
                Text(
                  '$orderCount orders',
                  style: AppTextStyles.caption,
                ),
                const Spacer(),
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 8,
                    vertical: 2,
                  ),
                  decoration: BoxDecoration(
                    color: isActive
                        ? AppColors.success.withOpacity(0.1)
                        : AppColors.textHint.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    isActive ? 'Active' : 'Inactive',
                    style: AppTextStyles.caption.copyWith(
                      color: isActive ? AppColors.success : AppColors.textHint,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
              ],
            ),
          ],
        ),
        trailing: const Icon(Icons.chevron_right),
        onTap: () {
          Navigator.pushNamed(
            context,
            '/branch-detail',
            arguments: branch,
          );
        },
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
