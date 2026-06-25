import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shared_core/shared_core.dart';
import '../../providers/inventory_provider.dart';

class StockDetailScreen extends StatefulWidget {
  final Map<String, dynamic>? item;

  const StockDetailScreen({super.key, this.item});

  @override
  State<StockDetailScreen> createState() => _StockDetailScreenState();
}

class _StockDetailScreenState extends State<StockDetailScreen> {
  late Map<String, dynamic> _item;

  @override
  void initState() {
    super.initState();
    _item = widget.item ?? {};
  }

  @override
  Widget build(BuildContext context) {
    final id = _item['id'] as int? ?? 0;
    final name = _item['name'] as String? ?? '';
    final category = _item['category'] as String? ?? '';
    final stock = _item['stock_quantity'] as int? ?? 0;
    final reorder = _item['reorder_level'] as int? ?? 0;
    final unit = _item['unit'] as String? ?? 'pcs';
    final price = ( _item['selling_price'] as num?)?.toDouble() ?? 0;
    final images = _item['images'] as List<dynamic>? ?? [];

    final stockRatio = reorder > 0 ? (stock / reorder).clamp(0, 2) : 1.0;
    final stockProgress = (stockRatio / 2).clamp(0, 1);

    return Scaffold(
      appBar: AppBar(title: Text(name)),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Center(
              child: Container(
                width: double.infinity,
                height: 200,
                decoration: BoxDecoration(
                  color: AppColors.surfaceVariant,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: images.isNotEmpty
                    ? ClipRRect(
                        borderRadius: BorderRadius.circular(12),
                        child: Image.network(
                          images.first as String,
                          fit: BoxFit.cover,
                          errorBuilder: (_, __, ___) => _imagePlaceholder(),
                        ),
                      )
                    : _imagePlaceholder(),
              ),
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(
                  child: Text(name, style: AppTextStyles.headlineMedium),
                ),
                Text(
                  Formatters.formatCurrency(price),
                  style: AppTextStyles.price,
                ),
              ],
            ),
            const SizedBox(height: 8),
            Chip(
              label: Text(category, style: AppTextStyles.caption),
            ),
            const SizedBox(height: 24),
            Text('Stock Level', style: AppTextStyles.titleLarge),
            const SizedBox(height: 8),
            Row(
              children: [
                Text(
                  '$stock $unit',
                  style: AppTextStyles.displaySmall.copyWith(
                    color: stock <= reorder ? AppColors.error : AppColors.success,
                  ),
                ),
                if (reorder > 0) ...[
                  const SizedBox(width: 8),
                  Text(
                    '/ $reorder reorder level',
                    style: AppTextStyles.bodySmall,
                  ),
                ],
              ],
            ),
            if (reorder > 0) ...[
              const SizedBox(height: 8),
              ClipRRect(
                borderRadius: BorderRadius.circular(6),
                child: LinearProgressIndicator(
                  value: stockProgress,
                  minHeight: 12,
                  backgroundColor: AppColors.surfaceVariant,
                  valueColor: AlwaysStoppedAnimation<Color>(
                    stock <= reorder ? AppColors.error : AppColors.success,
                  ),
                ),
              ),
            ],
            const SizedBox(height: 24),
            Row(
              children: [
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: () => _adjustStock(context, id, 1),
                    icon: const Icon(Icons.add),
                    label: const Text('Receive Stock'),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: () => _adjustStock(context, id, -1),
                    icon: const Icon(Icons.remove),
                    label: const Text('Adjust Stock'),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            SizedBox(
              width: double.infinity,
              child: OutlinedButton.icon(
                onPressed: () {},
                icon: const Icon(Icons.swap_horiz),
                label: const Text('Transfer to Branch'),
              ),
            ),
            const SizedBox(height: 24),
            Text('Movement History', style: AppTextStyles.titleLarge),
            const SizedBox(height: 8),
            _buildMovementHistory(),
          ],
        ),
      ),
    );
  }

  Widget _imagePlaceholder() {
    return const Center(
      child: Icon(Icons.image, size: 64, color: AppColors.textHint),
    );
  }

  Widget _buildMovementHistory() {
    final history = _item['movement_history'] as List<dynamic>? ?? [];
    if (history.isEmpty) {
      return const Card(
        child: Padding(
          padding: EdgeInsets.all(24),
          child: Center(
            child: Text('No movement history', style: AppTextStyles.bodySmall),
          ),
        ),
      );
    }
    return Column(
      children: history.map((m) {
        final move = m as Map<String, dynamic>;
        final date = move['date'] as String? ?? '';
        final type = move['type'] as String? ?? '';
        final qty = move['quantity'] as int? ?? 0;
        final who = move['done_by'] as String? ?? 'Staff';
        IconData icon;
        Color color;
        switch (type.toLowerCase()) {
          case 'received':
            icon = Icons.add_circle;
            color = AppColors.success;
            break;
          case 'sold':
            icon = Icons.shopping_cart;
            color = AppColors.primary;
            break;
          default:
            icon = Icons.swap_vert;
            color = AppColors.warning;
        }
        return Card(
          margin: const EdgeInsets.only(bottom: 4),
          child: ListTile(
            leading: Icon(icon, color: color),
            title: Text('${type[0].toUpperCase()}${type.substring(1)}',
                style: AppTextStyles.titleMedium),
            subtitle: Text('$who • ${Formatters.formatDate(date)}',
                style: AppTextStyles.caption),
            trailing: Text(
              qty >= 0 ? '+$qty' : '$qty',
              style: AppTextStyles.titleMedium.copyWith(color: color),
            ),
          ),
        );
      }).toList(),
    );
  }

  void _adjustStock(BuildContext context, int itemId, int direction) {
    final controller = TextEditingController(text: '1');
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(direction > 0 ? 'Receive Stock' : 'Adjust Stock'),
        content: TextField(
          controller: controller,
          keyboardType: TextInputType.number,
          decoration: const InputDecoration(labelText: 'Quantity'),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () {
              final qty = int.tryParse(controller.text);
              if (qty == null || qty <= 0) return;
              context.read<InventoryProvider>().adjustStock(
                    itemId,
                    direction > 0 ? qty : -qty,
                    direction > 0 ? 'Stock received' : 'Manual adjustment',
                  );
              Navigator.pop(ctx);
            },
            child: const Text('Confirm'),
          ),
        ],
      ),
    );
  }
}
