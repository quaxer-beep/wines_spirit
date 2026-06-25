import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shared_core/shared_core.dart';
import '../../providers/order_provider.dart';

class OrderDetailScreen extends StatefulWidget {
  final int orderId;
  const OrderDetailScreen({super.key, required this.orderId});

  @override
  State<OrderDetailScreen> createState() => _OrderDetailScreenState();
}

class _OrderDetailScreenState extends State<OrderDetailScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<OrderProvider>().loadOrderDetail(widget.orderId);
    });
  }

  @override
  Widget build(BuildContext context) {
    final orderProvider = context.watch<OrderProvider>();
    final order = orderProvider.currentOrder;

    return Scaffold(
      appBar: AppBar(title: Text('Order #${widget.orderId}')),
      body: orderProvider.isLoading
          ? const Center(child: CircularProgressIndicator())
          : order == null
              ? const ErrorDisplay(message: 'Order not found')
              : RefreshIndicator(
                  onRefresh: () =>
                      orderProvider.loadOrderDetail(widget.orderId),
                  child: SingleChildScrollView(
                    physics: const AlwaysScrollableScrollPhysics(),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Container(
                          width: double.infinity,
                          padding: const EdgeInsets.all(16),
                          color: AppColors.primary.withAlpha(12),
                          child: Column(
                            children: [
                              Text(order.orderNumber,
                                  style: AppTextStyles.headlineSmall),
                              const SizedBox(height: 8),
                              Text(order.formattedTotal,
                                  style: AppTextStyles.displayMedium
                                      ?.copyWith(color: AppColors.primary)),
                              const SizedBox(height: 8),
                              _buildStatusBadge(order.status),
                            ],
                          ),
                        ),
                        const SizedBox(height: 16),
                        Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 16),
                          child: Text('Order Timeline',
                              style: AppTextStyles.titleLarge),
                        ),
                        OrderTimeline(currentIndex: order.statusIndex),
                        const SizedBox(height: 16),
                        Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 16),
                          child: Text('Items',
                              style: AppTextStyles.titleLarge),
                        ),
                        ...order.items.map((item) => Card(
                              margin: const EdgeInsets.symmetric(
                                  horizontal: 16, vertical: 4),
                              child: ListTile(
                                title: Text(item.productName),
                                subtitle: Text('x${item.quantity}'),
                                trailing: Text(
                                  'KSh ${item.subtotal.toStringAsFixed(0)}',
                                  style: AppTextStyles.priceSmall,
                                ),
                              ),
                            )),
                        const SizedBox(height: 16),
                        Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 16),
                          child: Card(
                            child: Padding(
                              padding: const EdgeInsets.all(16),
                              child: Column(
                                children: [
                                  _detailRow(
                                      'Subtotal', order.subtotal),
                                  _detailRow(
                                      'Delivery', order.deliveryFee),
                                  if (order.discount > 0)
                                    _detailRow(
                                        'Discount', -order.discount),
                                  const Divider(),
                                  _detailRow('Total', order.grandTotal,
                                      bold: true),
                                ],
                              ),
                            ),
                          ),
                        ),
                        if (order.payments.isNotEmpty) ...[
                          const SizedBox(height: 16),
                          Padding(
                            padding:
                                const EdgeInsets.symmetric(horizontal: 16),
                            child: Text('Payment',
                                style: AppTextStyles.titleLarge),
                          ),
                          ...order.payments.map((p) => Card(
                                margin: const EdgeInsets.symmetric(
                                    horizontal: 16, vertical: 4),
                                child: ListTile(
                                  leading: const Icon(Icons.monetization_on),
                                  title:
                                      Text('${p.method} - ${p.status}'),
                                  subtitle: p.receiptNumber != null
                                      ? Text('Receipt: ${p.receiptNumber}')
                                      : null,
                                  trailing: Text(
                                    'KSh ${p.amount.toStringAsFixed(0)}',
                                    style: AppTextStyles.priceSmall,
                                  ),
                                ),
                              )),
                        ],
                        const SizedBox(height: 32),
                      ],
                    ),
                  ),
                ),
    );
  }

  Widget _buildStatusBadge(String status) {
    final color = AppColors.statusColor(status);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      decoration: BoxDecoration(
        color: color.withAlpha(25),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Text(
        status.toUpperCase(),
        style: TextStyle(
          color: color,
          fontWeight: FontWeight.bold,
          fontSize: 12,
        ),
      ),
    );
  }

  Widget _detailRow(String label, double amount, {bool bold = false}) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label,
              style: bold ? AppTextStyles.titleMedium : AppTextStyles.bodyMedium),
          Text(
            'KSh ${amount.abs().toStringAsFixed(0)}',
            style: bold
                ? AppTextStyles.titleLarge?.copyWith(color: AppColors.primary)
                : AppTextStyles.bodyMedium,
          ),
        ],
      ),
    );
  }
}
