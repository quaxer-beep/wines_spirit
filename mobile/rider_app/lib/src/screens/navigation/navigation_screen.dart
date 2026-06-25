import 'package:flutter/material.dart';
import 'package:shared_core/shared_core.dart';

class NavigationScreen extends StatelessWidget {
  final RiderDelivery delivery;

  const NavigationScreen({super.key, required this.delivery});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Navigation'),
        actions: [
          IconButton(
            icon: const Icon(Icons.help_outline),
            onPressed: () {
              Navigator.pushNamed(
                context,
                '/incident-report',
                arguments: delivery,
              );
            },
          ),
        ],
      ),
      body: Stack(
        children: [
          Container(
            width: double.infinity,
            height: double.infinity,
            color: AppColors.surfaceVariant,
            child: Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.map, size: 120, color: AppColors.textHint),
                  const SizedBox(height: 16),
                  Text(
                    'Map View',
                    style: AppTextStyles.headlineMedium,
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Navigation map will be displayed here',
                    style: AppTextStyles.bodySmall,
                  ),
                ],
              ),
            ),
          ),
          Positioned(
            top: 16,
            left: 16,
            right: 16,
            child: Card(
              margin: EdgeInsets.zero,
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Icon(Icons.location_on, color: AppColors.primary),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            delivery.address,
                            style: AppTextStyles.titleMedium,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        Icon(Icons.person_outline,
                            size: 16, color: AppColors.textSecondary),
                        const SizedBox(width: 4),
                        Text(
                          delivery.customerName ?? 'Customer',
                          style: AppTextStyles.bodySmall,
                        ),
                        const SizedBox(width: 16),
                        if (delivery.distanceKm != null) ...[
                          Icon(Icons.map_outlined,
                              size: 16, color: AppColors.textSecondary),
                          const SizedBox(width: 4),
                          Text(
                            '${delivery.distanceKm!.toStringAsFixed(1)} km',
                            style: AppTextStyles.bodySmall,
                          ),
                        ],
                      ],
                    ),
                    if (delivery.notes != null &&
                        delivery.notes!.isNotEmpty) ...[
                      const SizedBox(height: 8),
                      Container(
                        padding: const EdgeInsets.all(8),
                        decoration: BoxDecoration(
                          color: AppColors.info.withOpacity(0.1),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Row(
                          children: [
                            Icon(Icons.info_outline,
                                size: 14, color: AppColors.info),
                            const SizedBox(width: 8),
                            Expanded(
                              child: Text(
                                delivery.notes!,
                                style: AppTextStyles.bodySmall,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            ),
          ),
          Positioned(
            bottom: 32,
            left: 16,
            right: 16,
            child: Column(
              children: [
                Card(
                  margin: EdgeInsets.zero,
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceAround,
                      children: [
                        Column(
                          children: [
                            Text('ETA', style: AppTextStyles.caption),
                            const SizedBox(height: 4),
                            Text('-- min', style: AppTextStyles.titleMedium),
                          ],
                        ),
                        Column(
                          children: [
                            Text('Distance', style: AppTextStyles.caption),
                            const SizedBox(height: 4),
                            Text(
                              delivery.distanceKm != null
                                  ? '${delivery.distanceKm!.toStringAsFixed(1)} km'
                                  : '-- km',
                              style: AppTextStyles.titleMedium,
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 12),
                SizedBox(
                  width: double.infinity,
                  height: 56,
                  child: ElevatedButton.icon(
                    onPressed: () {},
                    icon: const Icon(Icons.navigation),
                    label: const Text('Start Navigation'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.primary,
                      foregroundColor: Colors.white,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
