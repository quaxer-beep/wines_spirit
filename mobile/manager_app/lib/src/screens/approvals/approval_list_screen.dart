import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shared_core/shared_core.dart';
import '../../providers/approval_provider.dart';

class ApprovalListScreen extends StatefulWidget {
  const ApprovalListScreen({super.key});

  @override
  State<ApprovalListScreen> createState() => _ApprovalListScreenState();
}

class _ApprovalListScreenState extends State<ApprovalListScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<ApprovalProvider>().fetchApprovals();
    });
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Approvals'),
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(text: 'Pending'),
            Tab(text: 'Approved'),
            Tab(text: 'Rejected'),
          ],
        ),
      ),
      body: Consumer<ApprovalProvider>(
        builder: (context, provider, _) {
          if (provider.isLoading && provider.pendingApprovals.isEmpty) {
            return const ShimmerLoading(itemCount: 5, itemBuilder: _shimmerItem);
          }
          if (provider.error != null) {
            return ErrorDisplay(
              message: provider.error!,
              onRetry: () => provider.fetchApprovals(),
            );
          }
          return TabBarView(
            controller: _tabController,
            children: [
              _buildList(provider.pendingApprovals, isPending: true),
              _buildList(provider.approvedApprovals),
              _buildList(provider.rejectedApprovals),
            ],
          );
        },
      ),
    );
  }

  Widget _buildList(List<Map<String, dynamic>> items, {bool isPending = false}) {
    if (items.isEmpty) {
      return const EmptyState(
        icon: Icons.approval,
        title: 'No approvals',
        subtitle: 'All caught up!',
      );
    }
    return RefreshIndicator(
      onRefresh: () => context.read<ApprovalProvider>().fetchApprovals(),
      child: ListView.builder(
        padding: const EdgeInsets.symmetric(vertical: 8),
        itemCount: items.length,
        itemBuilder: (context, index) {
          final item = items[index];
          return _buildApprovalCard(item, isPending);
        },
      ),
    );
  }

  Widget _buildApprovalCard(Map<String, dynamic> item, bool isPending) {
    final id = item['id'] as int? ?? 0;
    final type = item['type'] as String? ?? '';
    final requester = item['requester_name'] as String? ?? item['requester'] as String? ?? 'Unknown';
    final amount = (item['amount'] as num?)?.toDouble();
    final itemName = item['item_name'] as String? ?? item['item'] as String? ?? '';
    final date = item['created_at'] as String? ?? item['date'] as String? ?? '';
    final reason = item['reason'] as String? ?? item['description'] as String? ?? '';

    IconData typeIcon;
    switch (type.toLowerCase()) {
      case 'refund':
        typeIcon = Icons.refresh;
        break;
      case 'price change':
        typeIcon = Icons.attach_money;
        break;
      case 'stock adjustment':
        typeIcon = Icons.inventory;
        break;
      case 'transfer':
        typeIcon = Icons.swap_horiz;
        break;
      default:
        typeIcon = Icons.description;
    }

    return Dismissible(
      key: ValueKey(id),
      background: Container(
        color: AppColors.success,
        alignment: Alignment.centerLeft,
        padding: const EdgeInsets.only(left: 24),
        child: const Icon(Icons.check, color: Colors.white),
      ),
      secondaryBackground: Container(
        color: AppColors.error,
        alignment: Alignment.centerRight,
        padding: const EdgeInsets.only(right: 24),
        child: const Icon(Icons.close, color: Colors.white),
      ),
      confirmDismiss: isPending ? (direction) async {
        if (direction == DismissDirection.startToEnd) {
          await context.read<ApprovalProvider>().approve(id, '');
          return false;
        } else {
          final reasonController = TextEditingController();
          final result = await showDialog<bool>(
            context: context,
            builder: (ctx) => AlertDialog(
              title: const Text('Reject'),
              content: TextField(
                controller: reasonController,
                decoration: const InputDecoration(labelText: 'Reason'),
              ),
              actions: [
                TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancel')),
                ElevatedButton(
                  onPressed: () {
                    Navigator.pop(ctx, true);
                  },
                  style: ElevatedButton.styleFrom(backgroundColor: AppColors.error),
                  child: const Text('Reject'),
                ),
              ],
            ),
          );
          if (result == true) {
            await context.read<ApprovalProvider>().reject(id, reasonController.text);
          }
          return false;
        }
      } : null,
      child: Card(
        margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
        child: ListTile(
          onTap: () => Navigator.of(context).pushNamed(
            '/approval-detail',
            arguments: item,
          ),
          leading: CircleAvatar(
            backgroundColor: AppColors.primaryLight.withValues(alpha: 0.15),
            child: Icon(typeIcon, color: AppColors.primary, size: 20),
          ),
          title: Text(type, style: AppTextStyles.titleMedium),
          subtitle: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(requester, style: AppTextStyles.caption),
              if (amount != null)
                Text(Formatters.formatCurrency(amount), style: AppTextStyles.caption),
              if (itemName.isNotEmpty)
                Text(itemName, style: AppTextStyles.caption),
              const SizedBox(height: 2),
              Text(
                '${Formatters.timeAgo(date)} • ${Formatters.formatDate(date)}',
                style: AppTextStyles.caption.copyWith(color: AppColors.textHint),
              ),
            ],
          ),
          trailing: isPending
              ? const Icon(Icons.swipe, size: 18, color: AppColors.textHint)
              : null,
        ),
      ),
    );
  }

  static Widget _shimmerItem(int index) {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      child: Container(
        height: 80,
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(height: 12, width: 120, color: Colors.grey[300]),
            const SizedBox(height: 6),
            Container(height: 10, width: 200, color: Colors.grey[300]),
          ],
        ),
      ),
    );
  }
}
