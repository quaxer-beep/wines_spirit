import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shared_core/shared_core.dart';
import '../../providers/rider_delivery_provider.dart';

class PaymentScreen extends StatefulWidget {
  final RiderDelivery delivery;

  const PaymentScreen({super.key, required this.delivery});

  @override
  State<PaymentScreen> createState() => _PaymentScreenState();
}

class _PaymentScreenState extends State<PaymentScreen> {
  final _phoneController = TextEditingController(text: '254');
  String _paymentStatus = 'idle';
  int? _paymentId;

  @override
  void initState() {
    super.initState();
    final delivery = widget.delivery;
    if (delivery.customerPhone != null) {
      _phoneController.text = delivery.customerPhone!;
    }
  }

  @override
  void dispose() {
    _phoneController.dispose();
    super.dispose();
  }

  Future<void> _sendStkPush() async {
    final phone = _phoneController.text.trim();
    if (phone.isEmpty) return;

    setState(() => _paymentStatus = 'pending');

    final provider = context.read<RiderDeliveryProvider>();
    final delivery = widget.delivery;
    final amount = delivery.deliveryFee;

    Map<String, dynamic>? result;
    if (_paymentId != null && _paymentStatus == 'failed') {
      result = await provider.retryPayment(_paymentId!);
    } else {
      result = await provider.initiatePayment(
        delivery.orderId,
        customerPhone: phone,
        amount: amount + delivery.deliveryFee,
      );
    }

    if (!mounted) return;

    if (result != null) {
      _paymentId = result['payment_id'] ?? result['id'];
      final status = result['status'] ?? '';
      setState(() {
        _paymentStatus = status == 'failed' ? 'failed' : 'success';
      });
    } else {
      setState(() => _paymentStatus = 'failed');
    }
  }

  @override
  Widget build(BuildContext context) {
    final delivery = widget.delivery;
    final provider = context.watch<RiderDeliveryProvider>();
    final amount = delivery.deliveryFee;
    final total = amount + delivery.deliveryFee;

    return Scaffold(
      appBar: AppBar(
        title: const Text('M-Pesa Payment'),
      ),
      body: LoadingOverlay(
        isLoading: provider.isLoading,
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
                      Text('Payment Details', style: AppTextStyles.titleMedium),
                      const SizedBox(height: 16),
                      _buildRow('Order #', '#${delivery.orderId}'),
                      const SizedBox(height: 8),
                      _buildRow('Customer', delivery.customerName ?? 'N/A'),
                      const DimDivider(),
                      _buildRow('Amount Due', 'KSh ${amount.toStringAsFixed(0)}'),
                      const SizedBox(height: 8),
                      _buildRow('Delivery Fee', 'KSh ${delivery.deliveryFee.toStringAsFixed(0)}'),
                      const DimDivider(),
                      _buildRow('Total Amount', 'KSh ${total.toStringAsFixed(0)}', isTotal: true),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 24),
              Text('Customer Phone Number', style: AppTextStyles.labelMedium),
              const SizedBox(height: 8),
              TextField(
                controller: _phoneController,
                keyboardType: TextInputType.phone,
                decoration: const InputDecoration(
                  border: OutlineInputBorder(),
                  hintText: '254XXXXXXXXX',
                  prefixText: '+',
                ),
              ),
              const SizedBox(height: 24),
              SizedBox(
                width: double.infinity,
                height: 52,
                child: ElevatedButton.icon(
                  onPressed: _paymentStatus == 'pending' ? null : _sendStkPush,
                  icon: Icon(
                    _paymentStatus == 'failed' ? Icons.refresh : Icons.payment,
                  ),
                  label: Text(
                    _paymentStatus == 'pending'
                        ? 'Sending...'
                        : _paymentStatus == 'failed'
                            ? 'Retry Payment'
                            : 'Send M-Pesa STK Push',
                  ),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.mpesaGreen,
                    foregroundColor: Colors.white,
                  ),
                ),
              ),
              const SizedBox(height: 16),
              if (_paymentStatus == 'pending')
                Card(
                  color: AppColors.info.withOpacity(0.1),
                  child: Padding(
                    padding: const EdgeInsets.all(12),
                    child: Row(
                      children: [
                        const SizedBox(
                          width: 20, height: 20,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        ),
                        const SizedBox(width: 12),
                        Text('Processing payment...', style: AppTextStyles.bodyMedium),
                      ],
                    ),
                  ),
                ),
              if (_paymentStatus == 'success')
                Card(
                  color: AppColors.success.withOpacity(0.1),
                  child: Padding(
                    padding: const EdgeInsets.all(12),
                    child: Row(
                      children: [
                        Icon(Icons.check_circle, color: AppColors.success, size: 24),
                        const SizedBox(width: 12),
                        Text('Payment successful!', style: AppTextStyles.success),
                      ],
                    ),
                  ),
                ),
              if (_paymentStatus == 'failed')
                Card(
                  color: AppColors.error.withOpacity(0.1),
                  child: Padding(
                    padding: const EdgeInsets.all(12),
                    child: Row(
                      children: [
                        Icon(Icons.error, color: AppColors.error, size: 24),
                        const SizedBox(width: 12),
                        Text('Payment failed. Please try again.', style: AppTextStyles.error),
                      ],
                    ),
                  ),
                ),
              if (_paymentStatus == 'success')
                Padding(
                  padding: const EdgeInsets.only(top: 16),
                  child: SizedBox(
                    width: double.infinity,
                    height: 52,
                    child: ElevatedButton.icon(
                      onPressed: () => Navigator.pop(context, true),
                      icon: const Icon(Icons.check),
                      label: const Text('Done'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppColors.success,
                        foregroundColor: Colors.white,
                      ),
                    ),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildRow(String label, String value, {bool isTotal = false}) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(label, style: isTotal ? AppTextStyles.titleMedium : AppTextStyles.bodySmall),
        Text(value, style: isTotal ? AppTextStyles.price : AppTextStyles.bodyMedium),
      ],
    );
  }
}

class DimDivider extends StatelessWidget {
  const DimDivider({super.key});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Divider(color: AppColors.divider, height: 1),
    );
  }
}
