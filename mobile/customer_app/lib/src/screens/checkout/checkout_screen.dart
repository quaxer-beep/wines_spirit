import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shared_core/shared_core.dart';
import '../../providers/cart_provider.dart';
import '../../providers/order_provider.dart';

class CheckoutScreen extends StatefulWidget {
  const CheckoutScreen({super.key});
  @override
  State<CheckoutScreen> createState() => _CheckoutScreenState();
}

class _CheckoutScreenState extends State<CheckoutScreen> {
  int? _selectedAddressId;
  bool _useLoyalty = false;
  bool _isProcessing = false;

  Future<void> _placeOrder() async {
    if (_selectedAddressId == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please select a delivery address')),
      );
      return;
    }
    setState(() => _isProcessing = true);
    final orderProvider = context.read<OrderProvider>();
    final cart = context.read<CartProvider>();
    final order = await orderProvider.placeOrder(
      addressId: _selectedAddressId!,
      deliveryFee: 200.0,
    );
    if (order != null && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Order placed! Pay on delivery via M-Pesa.'), backgroundColor: AppColors.success),
      );
      await cart.clearCart();
      Navigator.pushReplacementNamed(context, '/order/${order.id}');
    }
    if (mounted) setState(() => _isProcessing = false);
  }

  @override
  Widget build(BuildContext context) {
    final cart = context.watch<CartProvider>();
    return Scaffold(
      appBar: AppBar(title: const Text('Checkout')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Delivery Address', style: AppTextStyles.titleLarge),
            const SizedBox(height: 8),
            Card(
              child: ListTile(
                leading: const Icon(Icons.location_on),
                title: const Text('Home'),
                subtitle: const Text('123 Test Street, Nairobi'),
                trailing: const Icon(Icons.chevron_right),
                selected: _selectedAddressId == 1,
                onTap: () => setState(() => _selectedAddressId = 1),
              ),
            ),
            const SizedBox(height: 24),
            Text('Order Summary', style: AppTextStyles.titleLarge),
            const SizedBox(height: 8),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  children: [
                    _summaryRow('Subtotal', cart.subtotal),
                    _summaryRow('Delivery Fee', 200.0),
                    if (_useLoyalty) _summaryRow('Loyalty Discount', -50.0),
                    const Divider(),
                    _summaryRow('Total', cart.subtotal + 200.0, bold: true),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),
            Card(
              child: SwitchListTile(
                title: const Text('Use Loyalty Points'),
                subtitle: Text(_useLoyalty ? 'KSh 50.00 discount applied' : 'You have 500 points', style: AppTextStyles.bodySmall),
                value: _useLoyalty,
                onChanged: (v) => setState(() => _useLoyalty = v),
              ),
            ),
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: AppColors.info.withOpacity(0.1),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Row(
                children: [
                  Icon(Icons.info_outline, size: 16, color: AppColors.info),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text('Payment will be collected upon delivery via M-Pesa STK Push.', style: AppTextStyles.bodySmall),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),
            SizedBox(
              width: double.infinity,
              height: 52,
              child: ElevatedButton(
                onPressed: _isProcessing ? null : _placeOrder,
                child: _isProcessing
                    ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2))
                    : const Text('Place Order'),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _summaryRow(String label, double amount, {bool bold = false}) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: bold ? AppTextStyles.titleMedium : AppTextStyles.bodyMedium),
          Text('KSh ${amount.abs().toStringAsFixed(0)}', style: bold ? AppTextStyles.titleLarge?.copyWith(color: AppColors.primary) : AppTextStyles.bodyMedium),
        ],
      ),
    );
  }
}
