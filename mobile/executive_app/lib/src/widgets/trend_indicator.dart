import 'package:flutter/material.dart';
import 'package:shared_core/shared_core.dart';

enum TrendIndicatorSize { small, large }

class TrendIndicator extends StatelessWidget {
  final double percentage;
  final TrendIndicatorSize size;

  const TrendIndicator({
    super.key,
    required this.percentage,
    this.size = TrendIndicatorSize.small,
  });

  @override
  Widget build(BuildContext context) {
    final isPositive = percentage >= 0;
    final color = isPositive ? AppColors.success : AppColors.error;

    final icon = Icon(
      isPositive ? Icons.arrow_upward : Icons.arrow_downward,
      color: color,
      size: size == TrendIndicatorSize.small ? 14 : 20,
    );

    final text = Text(
      '${isPositive ? '+' : ''}${percentage.toStringAsFixed(1)}%',
      style: (size == TrendIndicatorSize.small
              ? AppTextStyles.caption
              : AppTextStyles.bodyMedium)
          .copyWith(color: color, fontWeight: FontWeight.w600),
    );

    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [icon, const SizedBox(width: 2), text],
    );
  }
}
