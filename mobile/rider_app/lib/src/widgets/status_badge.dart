import 'package:flutter/material.dart';
import 'package:shared_core/shared_core.dart';

class StatusBadge extends StatelessWidget {
  final String status;
  final double fontSize;

  const StatusBadge({
    super.key,
    required this.status,
    this.fontSize = 11,
  });

  Color get _color {
    switch (status.toLowerCase()) {
      case 'pending':
      case 'assigned':
        return AppColors.textHint;
      case 'accepted':
        return AppColors.info;
      case 'picked_up':
        return AppColors.warning;
      case 'in_transit':
      case 'en_route':
        return const Color(0xFF7B1FA2);
      case 'age_verified':
        return AppColors.ageVerified;
      case 'payment_successful':
        return AppColors.mpesaGreen;
      case 'delivered':
      case 'resolved':
        return AppColors.success;
      case 'cancelled':
      case 'failed':
      case 'open':
        return AppColors.error;
      default:
        return AppColors.textSecondary;
    }
  }

  String get _label {
    switch (status.toLowerCase()) {
      case 'picked_up':
        return 'Preparing';
      case 'in_transit':
        return 'In Transit';
      case 'en_route':
        return 'Out for Delivery';
      case 'age_verified':
        return 'Age Verified';
      case 'payment_successful':
        return 'Payment Done';
      default:
        return status[0].toUpperCase() + status.substring(1);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: _color.withOpacity(0.15),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: _color.withOpacity(0.4)),
      ),
      child: Text(
        _label,
        style: TextStyle(
          fontSize: fontSize,
          fontWeight: FontWeight.w600,
          color: _color,
        ),
      ),
    );
  }
}
