import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shared_core/shared_core.dart';
import '../../providers/inventory_provider.dart';

class InventoryScreen extends StatefulWidget {
  const InventoryScreen({super.key});

  @override
  State<InventoryScreen> createState() => _InventoryScreenState();
}

class _InventoryScreenState extends State<InventoryScreen> {
  final _searchController = TextEditingController();
  String? _selectedCategory;
  bool _lowStockOnly = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<InventoryProvider>().fetchInventory();
    });
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  List<Map<String, dynamic>> _filteredItems(InventoryProvider provider) {
    var items = provider.stockItems;
    if (_lowStockOnly) {
      items = items.where((item) {
        final stock = item['stock_quantity'] as int? ?? 0;
        final reorder = item['reorder_level'] as int? ?? 0;
        return stock <= reorder;
      }).toList();
    }
    if (_selectedCategory != null) {
      items = items
          .where((item) => item['category']?.toString() == _selectedCategory)
          .toList();
    }
    return items;
  }

  Set<String> _categories(InventoryProvider provider) {
    return provider.stockItems
        .map((item) => item['category']?.toString() ?? 'Uncategorized')
        .toSet();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Inventory')),
      body: Consumer<InventoryProvider>(
        builder: (context, provider, _) {
          if (provider.isLoading && provider.stockItems.isEmpty) {
            return const ShimmerLoading(itemCount: 6, itemBuilder: _shimmerItem);
          }
          if (provider.error != null && provider.stockItems.isEmpty) {
            return ErrorDisplay(
              message: provider.error!,
              onRetry: () => provider.fetchInventory(),
            );
          }
          final items = _filteredItems(provider);
          return RefreshIndicator(
            onRefresh: () => provider.fetchInventory(),
            child: CustomScrollView(
              slivers: [
                SliverToBoxAdapter(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        TextField(
                          controller: _searchController,
                          decoration: const InputDecoration(
                            hintText: 'Search products...',
                            prefixIcon: Icon(Icons.search),
                          ),
                          onChanged: (q) {
                            provider.searchInventory(q);
                          },
                        ),
                        const SizedBox(height: 12),
                        Row(
                          children: [
                            Expanded(
                              child: SizedBox(
                                height: 36,
                                child: ListView(
                                  scrollDirection: Axis.horizontal,
                                  children: [
                                    FilterChip(
                                      label: const Text('All'),
                                      selected: _selectedCategory == null,
                                      onSelected: (_) => setState(() => _selectedCategory = null),
                                    ),
                                    const SizedBox(width: 8),
                                    ..._categories(provider).map((cat) {
                                      return Padding(
                                        padding: const EdgeInsets.only(right: 8),
                                        child: FilterChip(
                                          label: Text(cat),
                                          selected: _selectedCategory == cat,
                                          onSelected: (_) =>
                                              setState(() => _selectedCategory = cat),
                                        ),
                                      );
                                    }),
                                  ],
                                ),
                              ),
                            ),
                            const SizedBox(width: 8),
                            FilterChip(
                              label: const Text('Low Stock'),
                              selected: _lowStockOnly,
                              onSelected: (v) => setState(() => _lowStockOnly = v),
                              selectedColor: AppColors.error.withValues(alpha: 0.2),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ),
                if (items.isEmpty)
                  const SliverFillRemaining(
                    child: EmptyState(
                      icon: Icons.inventory_2_outlined,
                      title: 'No items found',
                    ),
                  )
                else
                  SliverList(
                    delegate: SliverChildBuilderDelegate(
                      (context, index) {
                        final item = items[index];
                        return _buildItemCard(item);
                      },
                      childCount: items.length,
                    ),
                  ),
              ],
            ),
          );
        },
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Stock adjustment coming soon')),
          );
        },
        child: const Icon(Icons.add),
      ),
    );
  }

  Widget _buildItemCard(Map<String, dynamic> item) {
    final name = item['name'] as String? ?? '';
    final category = item['category'] as String? ?? '';
    final stock = item['stock_quantity'] as int? ?? 0;
    final reorder = item['reorder_level'] as int? ?? 0;
    final unit = item['unit'] as String? ?? 'pcs';
    final price = (item['selling_price'] as num?)?.toDouble() ?? 0;

    Color stockColor;
    if (stock <= 0) {
      stockColor = AppColors.error;
    } else if (stock <= reorder) {
      stockColor = AppColors.warning;
    } else if (stock <= reorder * 2) {
      stockColor = AppColors.loyaltyGold;
    } else {
      stockColor = AppColors.success;
    }

    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      child: ListTile(
        onTap: () => Navigator.of(context).pushNamed(
          '/inventory-detail',
          arguments: item,
        ),
        title: Text(name, style: AppTextStyles.titleMedium),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const SizedBox(height: 4),
            Row(
              children: [
                Text('$category', style: AppTextStyles.caption),
                const SizedBox(width: 16),
                Text('KSh ${price.toStringAsFixed(0)}/$unit',
                    style: AppTextStyles.caption),
              ],
            ),
            const SizedBox(height: 4),
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                  decoration: BoxDecoration(
                    color: stockColor.withValues(alpha: 0.15),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    '$stock $unit',
                    style: AppTextStyles.caption.copyWith(
                      color: stockColor,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
                if (reorder > 0) ...[
                  const SizedBox(width: 8),
                  Text(
                    'Reorder: $reorder',
                    style: AppTextStyles.caption.copyWith(color: AppColors.textSecondary),
                  ),
                ],
              ],
            ),
          ],
        ),
        trailing: const Icon(Icons.chevron_right),
        isThreeLine: true,
      ),
    );
  }

  static Widget _shimmerItem(int index) {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      child: Container(
        height: 80,
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(height: 14, width: 150, color: Colors.grey[300]),
            const SizedBox(height: 8),
            Container(height: 12, width: 200, color: Colors.grey[300]),
          ],
        ),
      ),
    );
  }
}
