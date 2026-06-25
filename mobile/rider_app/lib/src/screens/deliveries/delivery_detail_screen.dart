import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shared_core/shared_core.dart';
import '../../providers/rider_delivery_provider.dart';
import '../../providers/rider_location_provider.dart';
import '../../widgets/status_badge.dart';

class DeliveryDetailScreen extends StatefulWidget {
  final RiderDelivery delivery;

  const DeliveryDetailScreen({super.key, required this.delivery});

  @override
  State<DeliveryDetailScreen> createState() => _DeliveryDetailScreenState();
}

class _DeliveryDetailScreenState extends State<DeliveryDetailScreen> {
  @override
  Widget build(BuildContext context) {
    final delivery = widget.delivery;
    final deliveryProvider = context.watch<RiderDeliveryProvider>();
    final locationProvider = context.watch<RiderLocationProvider>();

    return Scaffold(
      appBar: AppBar(
        title: Text('Delivery #${delivery.orderId}'),
      ),
      body: LoadingOverlay(
        isLoading: deliveryProvider.isLoading,
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _buildCustomerInfo(delivery),
              const SizedBox(height: 16),
              _buildDeliveryAddress(delivery),
              const SizedBox(height: 16),
              _buildOrderSummary(delivery),
              const SizedBox(height: 16),
              _buildStatusTimeline(delivery),
              const SizedBox(height: 24),
              _buildActionButtons(delivery, deliveryProvider, locationProvider),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildCustomerInfo(RiderDelivery delivery) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            CircleAvatar(
              backgroundColor: AppColors.primary.withOpacity(0.1),
              child: Text(
                (delivery.customerName ?? 'C')
                    .substring(0, 1)
                    .toUpperCase(),
                style: TextStyle(
                  color: AppColors.primary,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    delivery.customerName ?? 'Customer',
                    style: AppTextStyles.titleMedium,
                  ),
                  if (delivery.customerPhone != null)
                    Text(
                      delivery.customerPhone!,
                      style: AppTextStyles.bodySmall,
                    ),
                ],
              ),
            ),
            StatusBadge(status: delivery.status),
          ],
        ),
      ),
    );
  }

  Widget _buildDeliveryAddress(RiderDelivery delivery) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            Icon(Icons.location_on, color: AppColors.primary),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Delivery Address', style: AppTextStyles.labelMedium),
                  const SizedBox(height: 4),
                  Text(delivery.address, style: AppTextStyles.bodyMedium),
                  if (delivery.distanceKm != null) ...[
                    const SizedBox(height: 4),
                    Text(
                      '${delivery.distanceKm!.toStringAsFixed(1)} km away',
                      style: AppTextStyles.bodySmall,
                    ),
                  ],
                  if (delivery.notes != null && delivery.notes!.isNotEmpty) ...[
                    const SizedBox(height: 8),
                    Container(
                      padding: const EdgeInsets.all(8),
                      decoration: BoxDecoration(
                        color: AppColors.warning.withOpacity(0.1),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Row(
                        children: [
                          Icon(Icons.info_outline,
                              size: 16, color: AppColors.warning),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              delivery.notes!,
                              style: AppTextStyles.bodySmall,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildOrderSummary(RiderDelivery delivery) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Order Summary', style: AppTextStyles.titleMedium),
            const SizedBox(height: 12),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text('Order #', style: AppTextStyles.bodySmall),
                Text('#${delivery.orderId}', style: AppTextStyles.bodyMedium),
              ],
            ),
            const Divider(height: 16),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text('Delivery Fee', style: AppTextStyles.bodySmall),
                Text(
                  'KSh ${delivery.deliveryFee.toStringAsFixed(0)}',
                  style: AppTextStyles.priceSmall,
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStatusTimeline(RiderDelivery delivery) {
    final steps = [
      {'label': 'Ordered', 'icon': Icons.receipt_long, 'key': 'ordered'},
      {'label': 'Accepted', 'icon': Icons.check_circle_outline, 'key': 'accepted'},
      {'label': 'Preparing', 'icon': Icons.shopping_bag, 'key': 'picked_up'},
      {'label': 'Out for Delivery', 'icon': Icons.delivery_dining, 'key': 'en_route'},
      {'label': 'Age Verified', 'icon': Icons.verified_user, 'key': 'age_verified'},
      {'label': 'Payment Successful', 'icon': Icons.payment, 'key': 'payment_successful'},
      {'label': 'Delivered', 'icon': Icons.check_circle, 'key': 'delivered'},
    ];

    final currentIndex = steps.indexWhere(
      (s) => s['key'] == delivery.status,
    );

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Status Timeline', style: AppTextStyles.titleMedium),
            const SizedBox(height: 16),
            ...List.generate(steps.length, (index) {
              final step = steps[index];
              final isCompleted = index <= currentIndex && currentIndex >= 0;
              final isCurrent = index == currentIndex;
              return Row(
                children: [
                  Column(
                    children: [
                      Container(
                        width: 32,
                        height: 32,
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          color: isCompleted
                              ? AppColors.success
                              : AppColors.surfaceVariant,
                          border: isCurrent
                              ? Border.all(color: AppColors.primary, width: 2)
                              : null,
                        ),
                        child: Icon(
                          step['icon'] as IconData,
                          size: 16,
                          color: isCompleted ? Colors.white : AppColors.textHint,
                        ),
                      ),
                      if (index < steps.length - 1)
                        Container(
                          width: 2,
                          height: 24,
                          color: isCompleted
                              ? AppColors.success
                              : AppColors.divider,
                        ),
                    ],
                  ),
                  const SizedBox(width: 12),
                  Text(
                    step['label'] as String,
                    style: TextStyle(
                      fontSize: 14,
                      fontWeight:
                          isCurrent ? FontWeight.w600 : FontWeight.normal,
                      color: isCompleted
                          ? AppColors.textPrimary
                          : AppColors.textHint,
                    ),
                  ),
                ],
              );
            }),
          ],
        ),
      ),
    );
  }

  Widget _buildActionButtons(
    RiderDelivery delivery,
    RiderDeliveryProvider deliveryProvider,
    RiderLocationProvider locationProvider,
  ) {
    final List<Widget> buttons = [];

    if (delivery.status == 'assigned' || delivery.status == 'pending') {
      buttons.add(
        _ActionButton(
          label: 'Accept Delivery',
          icon: Icons.check_circle,
          color: AppColors.success,
          onPressed: () async {
            final ok = await deliveryProvider.acceptDelivery(delivery.id);
            if (ok && mounted) {
              locationProvider.startTracking();
              Navigator.pop(context, true);
            }
          },
        ),
      );
    }

    if (delivery.status == 'accepted') {
      buttons.add(
        _ActionButton(
          label: 'Mark Picked Up',
          icon: Icons.shopping_bag,
          color: AppColors.warning,
          onPressed: () async {
            final ok = await deliveryProvider.pickupDelivery(delivery.id);
            if (ok && mounted) Navigator.pop(context, true);
          },
        ),
      );
    }

    if (delivery.status == 'picked_up' || delivery.status == 'en_route') {
      buttons.add(
        _ActionButton(
          label: 'Start Navigation',
          icon: Icons.navigation,
          color: const Color(0xFF7B1FA2),
          onPressed: () {
            Navigator.pushNamed(context, '/navigation', arguments: delivery);
          },
        ),
      );
      buttons.add(
        _ActionButton(
          label: 'Verify Age',
          icon: Icons.verified_user,
          color: AppColors.success,
          onPressed: () => _showAgeVerificationDialog(delivery, deliveryProvider),
        ),
      );
    }

    if (delivery.status == 'age_verified') {
      buttons.add(
        _ActionButton(
          label: 'Collect Payment (M-Pesa STK Push)',
          icon: Icons.payment,
          color: AppColors.mpesaGreen,
          onPressed: () => _showPaymentDialog(delivery, deliveryProvider),
        ),
      );
    }

    if (delivery.status == 'payment_successful') {
      buttons.add(
        _ActionButton(
          label: 'Mark Delivered',
          icon: Icons.check_circle,
          color: AppColors.success,
          onPressed: () async {
            final ok = await deliveryProvider.completeDelivery(delivery.id);
            if (ok && mounted) Navigator.pop(context, true);
          },
        ),
      );
    }

    buttons.add(
      _ActionButton(
        label: 'Report Issue',
        icon: Icons.report_problem,
        color: AppColors.error,
        onPressed: () {
          Navigator.pushNamed(
            context,
            '/incident-report',
            arguments: delivery,
          );
        },
      ),
    );

    return Column(
      children: buttons,
    );
  }

  void _showAgeVerificationDialog(
    RiderDelivery delivery,
    RiderDeliveryProvider provider,
  ) {
    String selectedDocType = 'National ID';
    final docNumberController = TextEditingController();

    showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (context, setDialogState) {
          return AlertDialog(
            title: const Text('Age Verification'),
            content: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Verify customer age for Delivery #${delivery.orderId}',
                  style: AppTextStyles.bodySmall,
                ),
                const SizedBox(height: 16),
                Text('Document Type', style: AppTextStyles.labelMedium),
                const SizedBox(height: 8),
                DropdownButtonFormField<String>(
                  value: selectedDocType,
                  items: const [
                    DropdownMenuItem(value: 'National ID', child: Text('National ID')),
                    DropdownMenuItem(value: 'Passport', child: Text('Passport')),
                    DropdownMenuItem(value: 'Alien Card', child: Text('Alien Card')),
                  ],
                  onChanged: (v) {
                    if (v != null) setDialogState(() => selectedDocType = v);
                  },
                  decoration: const InputDecoration(
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 16),
                Text('Document Number', style: AppTextStyles.labelMedium),
                const SizedBox(height: 8),
                TextField(
                  controller: docNumberController,
                  decoration: const InputDecoration(
                    border: OutlineInputBorder(),
                    hintText: 'Enter document number',
                  ),
                ),
              ],
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(ctx),
                child: const Text('Cancel'),
              ),
              ElevatedButton(
                onPressed: () async {
                  final docNum = docNumberController.text.trim();
                  if (docNum.isEmpty) return;
                  final ok = await provider.verifyAge(
                    delivery.id,
                    documentType: selectedDocType,
                    documentNumber: docNum,
                  );
                  if (ok && mounted) {
                    Navigator.pop(ctx);
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Age verified successfully')),
                    );
                  }
                },
                child: const Text('Confirm'),
              ),
            ],
          );
        },
      ),
    );
  }

  void _showPaymentDialog(
    RiderDelivery delivery,
    RiderDeliveryProvider provider,
  ) {
    final phoneController = TextEditingController(
      text: delivery.customerPhone ?? '254',
    );
    String paymentStatus = 'idle';
    int? paymentId;
    final amount = delivery.deliveryFee;

    showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (context, setDialogState) {
          return AlertDialog(
            title: const Text('M-Pesa Payment'),
            content: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text('Order #', style: AppTextStyles.bodySmall),
                    Text('#${delivery.orderId}', style: AppTextStyles.bodyMedium),
                  ],
                ),
                const SizedBox(height: 8),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text('Customer', style: AppTextStyles.bodySmall),
                    Text(delivery.customerName ?? 'N/A', style: AppTextStyles.bodyMedium),
                  ],
                ),
                const Divider(),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text('Amount Due', style: AppTextStyles.bodySmall),
                    Text('KSh ${amount.toStringAsFixed(0)}', style: AppTextStyles.priceSmall),
                  ],
                ),
                const SizedBox(height: 8),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text('Delivery Fee', style: AppTextStyles.bodySmall),
                    Text('KSh ${delivery.deliveryFee.toStringAsFixed(0)}', style: AppTextStyles.priceSmall),
                  ],
                ),
                const Divider(),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text('Total', style: AppTextStyles.titleMedium),
                    Text('KSh ${(amount + delivery.deliveryFee).toStringAsFixed(0)}', style: AppTextStyles.price),
                  ],
                ),
                const SizedBox(height: 16),
                Text('Customer Phone', style: AppTextStyles.labelMedium),
                const SizedBox(height: 8),
                TextField(
                  controller: phoneController,
                  keyboardType: TextInputType.phone,
                  decoration: const InputDecoration(
                    border: OutlineInputBorder(),
                    hintText: '254XXXXXXXXX',
                  ),
                ),
                if (paymentStatus == 'pending') ...[
                  const SizedBox(height: 16),
                  Row(
                    children: [
                      const SizedBox(
                        width: 16, height: 16,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      ),
                      const SizedBox(width: 8),
                      Text('Processing payment...', style: AppTextStyles.bodySmall),
                    ],
                  ),
                ],
                if (paymentStatus == 'success') ...[
                  const SizedBox(height: 16),
                  Row(
                    children: [
                      Icon(Icons.check_circle, color: AppColors.success, size: 18),
                      const SizedBox(width: 8),
                      Text('Payment successful!', style: AppTextStyles.success),
                    ],
                  ),
                ],
                if (paymentStatus == 'failed') ...[
                  const SizedBox(height: 16),
                  Row(
                    children: [
                      Icon(Icons.error, color: AppColors.error, size: 18),
                      const SizedBox(width: 8),
                      Text('Payment failed', style: AppTextStyles.error),
                    ],
                  ),
                ],
              ],
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(ctx),
                child: const Text('Cancel'),
              ),
              if (paymentStatus == 'idle' || paymentStatus == 'failed')
                ElevatedButton.icon(
                  icon: Icon(paymentStatus == 'failed' ? Icons.refresh : Icons.payment),
                  label: Text(paymentStatus == 'failed' ? 'Retry' : 'Send M-Pesa STK Push'),
                  onPressed: () async {
                    final phone = phoneController.text.trim();
                    if (phone.isEmpty) return;
                    setDialogState(() => paymentStatus = 'pending');
                    Map<String, dynamic>? result;
                    if (paymentId != null && paymentStatus == 'failed') {
                      result = await provider.retryPayment(paymentId);
                    } else {
                      result = await provider.initiatePayment(
                        delivery.orderId,
                        customerPhone: phone,
                        amount: amount + delivery.deliveryFee,
                      );
                    }
                    if (result != null) {
                      paymentId = result['payment_id'] ?? result['id'];
                      final status = result['status'] ?? '';
                      setDialogState(() {
                        paymentStatus = status == 'failed' ? 'failed' : 'success';
                      });
                      if (paymentStatus == 'success' && mounted) {
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(content: Text('Payment collected successfully')),
                        );
                      }
                    } else {
                      setDialogState(() => paymentStatus = 'failed');
                    }
                  },
                ),
              if (paymentStatus == 'success')
                ElevatedButton(
                  onPressed: () => Navigator.pop(ctx),
                  child: const Text('Done'),
                ),
            ],
          );
        },
      ),
    );
  }
}

class _ActionButton extends StatelessWidget {
  final String label;
  final IconData icon;
  final Color color;
  final VoidCallback? onPressed;

  const _ActionButton({
    required this.label,
    required this.icon,
    required this.color,
    this.onPressed,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: SizedBox(
        width: double.infinity,
        height: 52,
        child: ElevatedButton.icon(
          onPressed: onPressed,
          icon: Icon(icon),
          label: Text(label),
          style: ElevatedButton.styleFrom(
            backgroundColor: color,
            foregroundColor: Colors.white,
          ),
        ),
      ),
    );
  }
}
