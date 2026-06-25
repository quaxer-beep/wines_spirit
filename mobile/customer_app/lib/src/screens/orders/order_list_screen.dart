import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shared_core/shared_core.dart';
import '../../providers/order_provider.dart';

class OrderListScreen extends StatefulWidget {
  const OrderListScreen({super.key});

  @override
  State<OrderListScreen> createState() => _OrderListScreenState();
}

class _OrderListScreenState extends State<OrderListScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<OrderProvider>().loadOrders();
    });
  }

  @override
  Widget build(BuildContext context) {
    final orderProvider = context.watch<OrderProvider>();
    return Scaffold(
      appBar: AppBar(title: const Text('My Orders')),
      body: orderProvider.isLoading
          ? const Center(child: CircularProgressIndicator())
          : orderProvider.orders.isEmpty
              ? const EmptyState(
                  icon: Icons.receipt_long,
                  title: 'No orders yet',
                  subtitle: 'Your order history will appear here',
                  actionLabel: 'Start Shopping',
                )
              : RefreshIndicator(
                  onRefresh: () => orderProvider.loadOrders(),
                  child: ListView.builder(
                    itemCount: orderProvider.orders.length,
                    itemBuilder: (context, index) {
                      final order = orderProvider.orders[index];
                      return OrderCard(
                        order: order,
                        onTap: () => Navigator.pushNamed(
                          context,
                          '/order/${order.id}',
                        ),
                      );
                    },
                  ),
                ),
    );
  }
}
