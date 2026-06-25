import 'package:flutter/material.dart';
import 'package:shared_core/shared_core.dart';

class StockAlertCard extends StatelessWidget {
  final String productName;
  final int currentStock;
  final int reorderLevel;
  final String category;
  final VoidCallback? onView;

  const StockAlertCard({
    super.key,
    required this.productName,
    required this.currentStock,
    required this.reorderLevel,
    required this.category,
    this.onView,
  });

  @override
  Widget build(BuildContext context) {
    final ratio = reorderLevel > 0 ? currentStock / reorderLevel : 1.0;
    final urgencyColor = ratio <= 0.25
        ? AppColors.error
        : ratio <= 0.75
            ? AppColors.warning
            : AppColors.success;

    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
      clipBehavior: Clip.antiAlias,
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(productName, style: AppTextStyles.titleMedium),
                  const SizedBox(height: 4),
                  Text(
                    '$currentStock / $reorderLevel',
                    style: AppTextStyles.bodyMedium.copyWith(
                      color: urgencyColor,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Container(
                    height: 6,
                    decoration: BoxDecoration(
                      color: AppColors.surfaceVariant,
                      borderRadius: BorderRadius.circular(3),
                    ),
                    child: FractionallySizedBox(
                      alignment: Alignment.centerLeft,
                      widthFactor: ratio.clamp(0, 1),
                      child: Container(
                        decoration: BoxDecoration(
                          color: urgencyColor,
                          borderRadius: BorderRadius.circular(3),
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(height: 6),
                  Chip(
                    label: Text(category, style: AppTextStyles.caption),
                    materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                    visualDensity: VisualDensity.compact,
                    padding: EdgeInsets.zero,
                    labelPadding: const EdgeInsets.symmetric(horizontal: 8),
                  ),
                ],
              ),
            ),
            if (onView != null)
              TextButton(
                onPressed: onView,
                child: const Text('View'),
              ),
          ],
        ),
      ),
    );
  }
}
