import 'package:flutter/material.dart';
import '../theme/app_colors.dart';
import '../theme/app_text_styles.dart';
import '../models/order.dart';
import '../utils/formatters.dart';

class OrderCard extends StatelessWidget {
  final Order order;
  final VoidCallback? onTap;

  const OrderCard({
    super.key,
    required this.order,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    order.orderNumber,
                    style: AppTextStyles.titleMedium,
                  ),
                  _buildStatusBadge(context),
                ],
              ),
              const SizedBox(height: 8),
              if (order.items.isNotEmpty)
                Text(
                  order.items.map((i) => i.productName).join(', '),
                  style: AppTextStyles.bodySmall,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
              const SizedBox(height: 8),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    Formatters.formatDate(order.createdAt),
                    style: AppTextStyles.caption,
                  ),
                  Text(
                    order.formattedTotal,
                    style: AppTextStyles.priceSmall,
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildStatusBadge(BuildContext context) {
    final color = AppColors.statusColor(order.status);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: color.withAlpha(25),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Text(
        order.statusLabel,
        style: TextStyle(fontSize: 12, fontWeight: FontWeight.w500, color: color),
      ),
    );
  }
}

class OrderTimeline extends StatelessWidget {
  final int currentIndex;

  const OrderTimeline({super.key, required this.currentIndex});

  @override
  Widget build(BuildContext context) {
    const steps = ['Pending', 'Confirmed', 'Preparing', 'Out for Delivery', 'Delivered'];
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        children: List.generate(steps.length, (index) {
          final isCompleted = index <= currentIndex;
          final isLast = index == steps.length - 1;
          return Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Column(
                children: [
                  Container(
                    width: 24,
                    height: 24,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: isCompleted ? AppColors.success : AppColors.surfaceVariant,
                      border: Border.all(
                        color: isCompleted ? AppColors.success : AppColors.border,
                        width: 2,
                      ),
                    ),
                    child: isCompleted
                        ? const Icon(Icons.check, size: 14, color: Colors.white)
                        : null,
                  ),
                  if (!isLast)
                    Container(
                      width: 2,
                      height: 32,
                      color: isCompleted ? AppColors.success : AppColors.border,
                    ),
                ],
              ),
              const SizedBox(width: 12),
              Padding(
                padding: EdgeInsets.only(bottom: isLast ? 0 : 20),
                child: Text(
                  steps[index],
                  style: TextStyle(
                    fontWeight: isCompleted ? FontWeight.w600 : FontWeight.normal,
                    color: isCompleted ? AppColors.textPrimary : AppColors.textHint,
                  ),
                ),
              ),
            ],
          );
        }),
      ),
    );
  }
}
