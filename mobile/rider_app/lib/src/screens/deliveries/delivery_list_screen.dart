import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shared_core/shared_core.dart';
import '../../providers/rider_delivery_provider.dart';
import '../../providers/rider_auth_provider.dart';
import '../../widgets/delivery_card.dart';

class DeliveryListScreen extends StatefulWidget {
  const DeliveryListScreen({super.key});

  @override
  State<DeliveryListScreen> createState() => _DeliveryListScreenState();
}

class _DeliveryListScreenState extends State<DeliveryListScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  bool _isOnline = true;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
    _loadDeliveries();
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  void _loadDeliveries() {
    context.read<RiderDeliveryProvider>().fetchDeliveries();
    context.read<RiderDeliveryProvider>().fetchActiveDeliveries();
  }

  @override
  Widget build(BuildContext context) {
    final deliveryProvider = context.watch<RiderDeliveryProvider>();
    return Scaffold(
      appBar: AppBar(
        title: Text(AppConstants.riderAppName),
        actions: [
          IconButton(
            icon: const Icon(Icons.person_outline),
            onPressed: () => Navigator.pushNamed(context, '/profile'),
          ),
        ],
        bottom: TabBar(
          controller: _tabController,
          labelColor: AppColors.textOnPrimary,
          unselectedLabelColor: AppColors.textOnPrimary.withOpacity(0.6),
          indicatorColor: AppColors.textOnPrimary,
          tabs: const [
            Tab(text: 'Available'),
            Tab(text: 'Active'),
            Tab(text: 'Completed'),
          ],
        ),
      ),
      body: RefreshIndicator(
        onRefresh: () async => _loadDeliveries(),
        child: TabBarView(
          controller: _tabController,
          children: [
            _buildAvailableTab(deliveryProvider),
            _buildActiveTab(deliveryProvider),
            _buildCompletedTab(deliveryProvider),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () {
          setState(() => _isOnline = !_isOnline);
        },
        icon: Icon(_isOnline ? Icons.wifi : Icons.wifi_off),
        label: Text(_isOnline ? 'Online' : 'Offline'),
        backgroundColor: _isOnline ? AppColors.success : AppColors.textHint,
      ),
    );
  }

  Widget _buildAvailableTab(RiderDeliveryProvider provider) {
    if (provider.isLoading && provider.deliveries.isEmpty) {
      return const ShimmerLoading();
    }
    final available = provider.deliveries
        .where((d) => d.status == 'assigned' || d.status == 'pending')
        .toList();
    if (available.isEmpty) {
      return EmptyState(
        icon: Icons.inbox_outlined,
        title: 'No Available Deliveries',
        subtitle: 'New deliveries will appear here',
      );
    }
    return ListView.builder(
      padding: const EdgeInsets.only(top: 8, bottom: 88),
      itemCount: available.length,
      itemBuilder: (context, index) {
        final delivery = available[index];
        return DeliveryCard(
          delivery: delivery,
          onTap: () => Navigator.pushNamed(
            context,
            '/delivery-detail',
            arguments: delivery,
          ),
          onAction: () => Navigator.pushNamed(
            context,
            '/delivery-detail',
            arguments: delivery,
          ),
        );
      },
    );
  }

  Widget _buildActiveTab(RiderDeliveryProvider provider) {
    if (provider.isLoading && provider.activeDeliveries.isEmpty) {
      return const ShimmerLoading();
    }
    if (provider.activeDeliveries.isEmpty) {
      return EmptyState(
        icon: Icons.directions_bike_outlined,
        title: 'No Active Deliveries',
        subtitle: 'Accept a delivery to get started',
      );
    }
    return ListView.builder(
      padding: const EdgeInsets.only(top: 8, bottom: 88),
      itemCount: provider.activeDeliveries.length,
      itemBuilder: (context, index) {
        final delivery = provider.activeDeliveries[index];
        return DeliveryCard(
          delivery: delivery,
          onTap: () => Navigator.pushNamed(
            context,
            '/delivery-detail',
            arguments: delivery,
          ),
          onAction: () => Navigator.pushNamed(
            context,
            '/delivery-detail',
            arguments: delivery,
          ),
        );
      },
    );
  }

  Widget _buildCompletedTab(RiderDeliveryProvider provider) {
    if (provider.isLoading && provider.deliveries.isEmpty) {
      return const ShimmerLoading();
    }
    final completed = provider.deliveries
        .where((d) => d.status == 'delivered' || d.status == 'failed')
        .toList();
    if (completed.isEmpty) {
      return EmptyState(
        icon: Icons.check_circle_outline,
        title: 'No Completed Deliveries',
        subtitle: 'Completed deliveries will appear here',
      );
    }
    return ListView.builder(
      padding: const EdgeInsets.only(top: 8, bottom: 88),
      itemCount: completed.length,
      itemBuilder: (context, index) {
        final delivery = completed[index];
        return DeliveryCard(
          delivery: delivery,
          onTap: () => Navigator.pushNamed(
            context,
            '/delivery-detail',
            arguments: delivery,
          ),
        );
      },
    );
  }
}
