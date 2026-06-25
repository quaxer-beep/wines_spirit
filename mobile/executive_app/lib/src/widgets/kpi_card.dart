import 'package:flutter/material.dart';
import 'package:shared_core/shared_core.dart';
import 'trend_indicator.dart';

class KpiCard extends StatelessWidget {
  final String label;
  final String value;
  final double? growthPercentage;
  final String? subtitle;
  final VoidCallback? onTap;
  final Widget? leading;

  const KpiCard({
    super.key,
    required this.label,
    required this.value,
    this.growthPercentage,
    this.subtitle,
    this.onTap,
    this.leading,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: EdgeInsets.zero,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              if (leading != null)
                Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: leading!,
                ),
              Text(
                value,
                style: AppTextStyles.displayMedium.copyWith(
                  color: growthPercentage != null && growthPercentage! < 0
                      ? AppColors.error
                      : AppColors.primary,
                  fontSize: 24,
                ),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
              const SizedBox(height: 4),
              Text(
                label,
                style: AppTextStyles.bodySmall,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
              if (growthPercentage != null) ...[
                const SizedBox(height: 4),
                TrendIndicator(
                  percentage: growthPercentage!,
                  size: TrendIndicatorSize.small,
                ),
              ],
              if (subtitle != null) ...[
                const SizedBox(height: 2),
                Text(
                  subtitle!,
                  style: AppTextStyles.caption,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
