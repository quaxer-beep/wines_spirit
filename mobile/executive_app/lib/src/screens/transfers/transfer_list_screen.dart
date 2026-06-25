import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shared_core/shared_core.dart';
import '../../providers/transfer_provider.dart';
import '../../widgets/transfer_card.dart';

class TransferListScreen extends StatefulWidget {
  const TransferListScreen({super.key});

  @override
  State<TransferListScreen> createState() => _TransferListScreenState();
}

class _TransferListScreenState extends State<TransferListScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<TransferProvider>().fetchTransfers();
    });
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  Future<void> _onRefresh() async {
    await context.read<TransferProvider>().fetchTransfers();
  }

  @override
  Widget build(BuildContext context) {
    final transferProvider = context.watch<TransferProvider>();

    final allTransfers = transferProvider.transfers;
    final pending = allTransfers
        .where((t) => (t['status'] ?? '').toString().toLowerCase() == 'pending')
        .toList();
    final approved = allTransfers
        .where((t) => (t['status'] ?? '').toString().toLowerCase() == 'approved')
        .toList();
    final rejected = allTransfers
        .where((t) => (t['status'] ?? '').toString().toLowerCase() == 'rejected')
        .toList();

    return Scaffold(
      appBar: AppBar(
        title: const Text('Transfers'),
        bottom: TabBar(
          controller: _tabController,
          indicatorColor: AppColors.loyaltyGold,
          labelColor: AppColors.primary,
          unselectedLabelColor: AppColors.textSecondary,
          tabs: const [
            Tab(text: 'All'),
            Tab(text: 'Pending'),
            Tab(text: 'Approved'),
            Tab(text: 'Rejected'),
          ],
        ),
      ),
      body: transferProvider.isLoading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _onRefresh,
              child: TabBarView(
                controller: _tabController,
                children: [
                  _buildList(allTransfers),
                  _buildList(pending),
                  _buildList(approved),
                  _buildList(rejected),
                ],
              ),
            ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {},
        child: const Icon(Icons.add),
      ),
    );
  }

  Widget _buildList(List<Map<String, dynamic>> transfers) {
    if (transfers.isEmpty) {
      return const Center(child: Text('No transfers'));
    }

    return ListView.builder(
      itemCount: transfers.length,
      itemBuilder: (context, index) {
        final transfer = transfers[index];
        return TransferCard(
          transfer: transfer,
          onTap: () {
            Navigator.pushNamed(
              context,
              '/transfer-detail',
              arguments: transfer,
            );
          },
        );
      },
    );
  }
}
