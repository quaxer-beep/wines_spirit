import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shared_core/shared_core.dart';
import '../../providers/approval_provider.dart';

class ApprovalDetailScreen extends StatefulWidget {
  final Map<String, dynamic>? approval;

  const ApprovalDetailScreen({super.key, this.approval});

  @override
  State<ApprovalDetailScreen> createState() => _ApprovalDetailScreenState();
}

class _ApprovalDetailScreenState extends State<ApprovalDetailScreen> {
  late Map<String, dynamic> _approval;
  final _noteController = TextEditingController();
  bool _isSubmitting = false;

  @override
  void initState() {
    super.initState();
    _approval = widget.approval ?? {};
  }

  @override
  void dispose() {
    _noteController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final id = _approval['id'] as int? ?? 0;
    final type = _approval['type'] as String? ?? '';
    final requester = _approval['requester_name'] as String? ??
        _approval['requester'] as String? ?? 'Unknown';
    final amount = (_approval['amount'] as num?)?.toDouble();
    final itemName = _approval['item_name'] as String? ??
        _approval['item'] as String? ?? '';
    final reason = _approval['reason'] as String? ??
        _approval['description'] as String? ?? '';
    final status = _approval['status'] as String? ?? 'pending';
    final date = _approval['created_at'] as String? ??
        _approval['date'] as String? ?? '';
    final supportingInfo = _approval['supporting_info'] as String? ??
        _approval['notes'] as String? ?? '';

    final isPending = status == 'pending';

    return Scaffold(
      appBar: AppBar(title: Text('$type Request')),
      body: Column(
        children: [
          Expanded(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Text(type, style: AppTextStyles.headlineMedium),
                              Container(
                                padding: const EdgeInsets.symmetric(
                                    horizontal: 12, vertical: 4),
                                decoration: BoxDecoration(
                                  color: AppColors.statusColor(status)
                                      .withValues(alpha: 0.15),
                                  borderRadius: BorderRadius.circular(12),
                                ),
                                child: Text(
                                  status.toUpperCase(),
                                  style: AppTextStyles.caption.copyWith(
                                    color: AppColors.statusColor(status),
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 16),
                          if (amount != null) ...[
                            _infoRow('Amount', Formatters.formatCurrency(amount)),
                            const Divider(),
                          ],
                          if (itemName.isNotEmpty) ...[
                            _infoRow('Item', itemName),
                            const Divider(),
                          ],
                          _infoRow('Requester', requester),
                          const Divider(),
                          _infoRow('Date', Formatters.formatDateTime(date)),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),
                  Text('Reason / Description', style: AppTextStyles.titleLarge),
                  const SizedBox(height: 8),
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Text(
                        reason.isNotEmpty ? reason : 'No description provided',
                        style: AppTextStyles.bodyMedium,
                      ),
                    ),
                  ),
                  if (supportingInfo.isNotEmpty) ...[
                    const SizedBox(height: 16),
                    Text('Supporting Information', style: AppTextStyles.titleLarge),
                    const SizedBox(height: 8),
                    Card(
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Text(supportingInfo, style: AppTextStyles.bodyMedium),
                      ),
                    ),
                  ],
                  if (isPending) ...[
                    const SizedBox(height: 16),
                    TextField(
                      controller: _noteController,
                      maxLines: 3,
                      decoration: const InputDecoration(
                        labelText: 'Note / Reason',
                        hintText: 'Add a note...',
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ),
          if (isPending)
            SafeArea(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Row(
                  children: [
                    Expanded(
                      child: ElevatedButton.icon(
                        onPressed: _isSubmitting
                            ? null
                            : () => _handleApprove(context, id),
                        icon: const Icon(Icons.check),
                        label: const Text('Approve'),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: AppColors.success,
                        ),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: ElevatedButton.icon(
                        onPressed: _isSubmitting
                            ? null
                            : () => _handleReject(context, id),
                        icon: const Icon(Icons.close),
                        label: const Text('Reject'),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: AppColors.error,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
        ],
      ),
    );
  }

  Widget _infoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: AppTextStyles.bodySmall),
          Text(value, style: AppTextStyles.bodyMedium),
        ],
      ),
    );
  }

  Future<void> _handleApprove(BuildContext context, int id) async {
    setState(() => _isSubmitting = true);
    final success = await context
        .read<ApprovalProvider>()
        .approve(id, _noteController.text.trim());
    if (!mounted) return;
    setState(() => _isSubmitting = false);
    if (success) Navigator.of(context).pop();
  }

  Future<void> _handleReject(BuildContext context, int id) async {
    setState(() => _isSubmitting = true);
    final success = await context
        .read<ApprovalProvider>()
        .reject(id, _noteController.text.trim());
    if (!mounted) return;
    setState(() => _isSubmitting = false);
    if (success) Navigator.of(context).pop();
  }
}
