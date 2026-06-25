import 'package:flutter/material.dart';
import 'package:shared_core/shared_core.dart';

class KpiCard extends StatelessWidget {
  final String title;
  final String value;
  final IconData icon;
  final double? trend;
  final Color accentColor;
  final VoidCallback? onTap;

  const KpiCard({
    super.key,
    required this.title,
    required this.value,
    required this.icon,
    this.trend,
    this.accentColor = AppColors.primary,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Card(
        margin: EdgeInsets.zero,
        clipBehavior: Clip.antiAlias,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(height: 4, color: accentColor),
            Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(title, style: AppTextStyles.bodySmall),
                      Icon(icon, size: 20, color: accentColor),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          value,
                          style: AppTextStyles.displaySmall.copyWith(
                            color: accentColor,
                            fontSize: 22,
                          ),
                        ),
                      ),
                      if (trend != null)
                        Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(
                              trend! >= 0 ? Icons.trending_up : Icons.trending_down,
                              size: 16,
                              color: trend! >= 0 ? AppColors.success : AppColors.error,
                            ),
                            Text(
                              '${trend!.abs().toStringAsFixed(1)}%',
                              style: AppTextStyles.caption.copyWith(
                                color: trend! >= 0 ? AppColors.success : AppColors.error,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ],
                        ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
