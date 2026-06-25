import 'package:flutter/material.dart';
import 'package:shared_core/shared_core.dart';
import 'status_badge.dart';

class DeliveryCard extends StatelessWidget {
  final RiderDelivery delivery;
  final VoidCallback? onTap;
  final VoidCallback? onAction;

  const DeliveryCard({
    super.key,
    required this.delivery,
    this.onTap,
    this.onAction,
  });

  IconData get _actionIcon {
    switch (delivery.status) {
      case 'assigned':
        return Icons.check_circle_outline;
      case 'accepted':
        return Icons.shopping_bag_outlined;
      case 'picked_up':
        return Icons.navigation;
      case 'en_route':
        return Icons.location_on;
      default:
        return Icons.arrow_forward_ios;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Text(
                          delivery.customerName ?? 'Customer',
                          style: AppTextStyles.titleMedium,
                        ),
                        const SizedBox(width: 8),
                        StatusBadge(status: delivery.status),
                      ],
                    ),
                    const SizedBox(height: 6),
                    Row(
                      children: [
                        Icon(Icons.location_on_outlined,
                            size: 14, color: AppColors.textSecondary),
                        const SizedBox(width: 4),
                        Expanded(
                          child: Text(
                            delivery.address,
                            style: AppTextStyles.bodySmall,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 6),
                    Row(
                      children: [
                        if (delivery.distanceKm != null) ...[
                          Icon(Icons.map_outlined,
                              size: 14, color: AppColors.textSecondary),
                          const SizedBox(width: 4),
                          Text(
                            '${delivery.distanceKm!.toStringAsFixed(1)} km',
                            style: AppTextStyles.caption,
                          ),
                          const SizedBox(width: 12),
                        ],
                        Text(
                          'Order #${delivery.orderId}',
                          style: AppTextStyles.caption,
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              Column(
                children: [
                  Text(
                    'KSh ${delivery.deliveryFee.toStringAsFixed(0)}',
                    style: AppTextStyles.priceSmall,
                  ),
                  const SizedBox(height: 8),
                  if (onAction != null)
                    IconButton(
                      onPressed: onAction,
                      icon: Icon(_actionIcon, color: AppColors.primary),
                      constraints: const BoxConstraints(
                        minWidth: 36,
                        minHeight: 36,
                      ),
                      padding: EdgeInsets.zero,
                    ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
