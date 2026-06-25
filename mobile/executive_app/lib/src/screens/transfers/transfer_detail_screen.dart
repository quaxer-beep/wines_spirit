import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shared_core/shared_core.dart';
import '../../providers/transfer_provider.dart';

class TransferDetailScreen extends StatelessWidget {
  final Map<String, dynamic> transfer;

  const TransferDetailScreen({super.key, required this.transfer});

  @override
  Widget build(BuildContext context) {
    final status = (transfer['status'] ?? '').toString();
    final statusColor = AppColors.statusColor(status);
    final fromBranch = transfer['from_branch'] ?? '';
    final toBranch = transfer['to_branch'] ?? '';
    final reference = transfer['reference'] ?? transfer['id'] ?? '';
    final totalValue = (transfer['total_value'] ?? 0).toDouble();
    final notes = transfer['notes'] ?? transfer['reason'] ?? '';
    final items = List<Map<String, dynamic>>.from(transfer['items'] ?? []);
    final timeline = List<Map<String, dynamic>>.from(transfer['timeline'] ?? []);
    final isPending = status.toLowerCase() == 'pending';

    return Scaffold(
      appBar: AppBar(
        title: Text(reference),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Card(
            margin: EdgeInsets.zero,
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: Column(
                          children: [
                            Icon(
                              Icons.store,
                              color: AppColors.primary,
                              size: 24,
                            ),
                            const SizedBox(height: 4),
                            Text(
                              fromBranch,
                              style: AppTextStyles.bodyMedium,
                              textAlign: TextAlign.center,
                            ),
                          ],
                        ),
                      ),
                      const Icon(Icons.arrow_forward, color: AppColors.textSecondary),
                      Expanded(
                        child: Column(
                          children: [
                            Icon(
                              Icons.store,
                              color: AppColors.success,
                              size: 24,
                            ),
                            const SizedBox(height: 4),
                            Text(
                              toBranch,
                              style: AppTextStyles.bodyMedium,
                              textAlign: TextAlign.center,
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 16,
                      vertical: 6,
                    ),
                    decoration: BoxDecoration(
                      color: statusColor.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Text(
                      status.toUpperCase(),
                      style: AppTextStyles.titleMedium.copyWith(
                        color: statusColor,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          if (items.isNotEmpty) ...[
            Text('Items', style: AppTextStyles.titleLarge),
            const SizedBox(height: 8),
            ...items.map((item) => Card(
                  margin: const EdgeInsets.only(bottom: 8),
                  child: Padding(
                    padding: const EdgeInsets.all(12),
                    child: Row(
                      children: [
                        Expanded(
                          flex: 3,
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                item['product'] ?? item['name'] ?? '',
                                style: AppTextStyles.bodyMedium,
                              ),
                              Text(
                                'Qty: ${item['quantity'] ?? 0}',
                                style: AppTextStyles.caption,
                              ),
                            ],
                          ),
                        ),
                        Text(
                          '\$${_formatValue((item['unit_value'] ?? 0).toDouble())}',
                          style: AppTextStyles.bodySmall,
                        ),
                        const SizedBox(width: 16),
                        Text(
                          '\$${_formatValue((item['total'] ?? 0).toDouble())}',
                          style: AppTextStyles.titleMedium.copyWith(
                            color: AppColors.primary,
                          ),
                        ),
                      ],
                    ),
                  ),
                )),
            const SizedBox(height: 8),
            Card(
              margin: EdgeInsets.zero,
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text('Total', style: AppTextStyles.titleLarge),
                    Text(
                      '\$${_formatValue(totalValue)}',
                      style: AppTextStyles.headlineMedium.copyWith(
                        color: AppColors.primary,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
          if (notes.isNotEmpty) ...[
            const SizedBox(height: 16),
            Text('Notes', style: AppTextStyles.titleLarge),
            const SizedBox(height: 8),
            Card(
              margin: EdgeInsets.zero,
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Text(
                  notes,
                  style: AppTextStyles.bodyMedium,
                ),
              ),
            ),
          ],
          if (timeline.isNotEmpty) ...[
            const SizedBox(height: 16),
            Text('Approval Timeline', style: AppTextStyles.titleLarge),
            const SizedBox(height: 8),
            ...timeline.map((entry) {
              final step = entry['step'] ?? '';
              final date = entry['date'] ?? '';
              final actor = entry['actor'] ?? '';
              final isCompleted = entry['completed'] == true;

              return Card(
                margin: const EdgeInsets.only(bottom: 8),
                child: ListTile(
                  leading: CircleAvatar(
                    backgroundColor: isCompleted
                        ? AppColors.success.withOpacity(0.1)
                        : AppColors.textHint.withOpacity(0.1),
                    child: Icon(
                      isCompleted ? Icons.check : Icons.schedule,
                      color: isCompleted ? AppColors.success : AppColors.textHint,
                      size: 20,
                    ),
                  ),
                  title: Text(step, style: AppTextStyles.bodyMedium),
                  subtitle: Text(
                    '$actor - $date',
                    style: AppTextStyles.caption,
                  ),
                ),
              );
            }),
          ],
          if (isPending) ...[
            const SizedBox(height: 24),
            Row(
              children: [
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: () => _handleApprove(context),
                    icon: const Icon(Icons.check),
                    label: const Text('Approve'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.success,
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(vertical: 14),
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: () => _handleReject(context),
                    icon: const Icon(Icons.close),
                    label: const Text('Reject'),
                    style: OutlinedButton.styleFrom(
                      foregroundColor: AppColors.error,
                      side: const BorderSide(color: AppColors.error),
                      padding: const EdgeInsets.symmetric(vertical: 14),
                    ),
                  ),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }

  Future<void> _handleApprove(BuildContext context) async {
    final provider = context.read<TransferProvider>();
    final id = transfer['id'] ?? '';
    final success = await provider.approveTransfer(id);
    if (!context.mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(success ? 'Transfer approved' : 'Failed to approve'),
      ),
    );
    if (success) Navigator.pop(context);
  }

  Future<void> _handleReject(BuildContext context) async {
    final reasonController = TextEditingController();
    final reason = await showDialog<String>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Reject Transfer'),
        content: TextField(
          controller: reasonController,
          decoration: const InputDecoration(
            hintText: 'Reason for rejection',
          ),
          maxLines: 3,
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(ctx, reasonController.text),
            child: const Text('Reject'),
          ),
        ],
      ),
    );

    if (reason == null || reason.isEmpty) return;

    final provider = context.read<TransferProvider>();
    final id = transfer['id'] ?? '';
    final success = await provider.rejectTransfer(id, reason);
    if (!context.mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(success ? 'Transfer rejected' : 'Failed to reject'),
      ),
    );
    if (success) Navigator.pop(context);
  }

  String _formatValue(double val) {
    if (val >= 1000000) {
      return '${(val / 1000000).toStringAsFixed(1)}M';
    } else if (val >= 1000) {
      return '${(val / 1000).toStringAsFixed(1)}K';
    }
    return val.toStringAsFixed(2);
  }
}
