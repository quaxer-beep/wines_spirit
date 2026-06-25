import 'package:flutter/material.dart';
import '../theme/app_colors.dart';

class AgeVerificationBadge extends StatelessWidget {
  final bool? isVerified;
  final String? status;
  final double size;

  const AgeVerificationBadge({
    super.key,
    this.isVerified,
    this.status,
    this.size = 16,
  });

  @override
  Widget build(BuildContext context) {
    Color color;
    IconData icon;
    String label;

    if (isVerified == true || status == 'approved') {
      color = AppColors.ageVerified;
      icon = Icons.verified;
      label = 'Age Verified';
    } else if (status == 'pending') {
      color = AppColors.agePending;
      icon = Icons.access_time;
      label = 'Verification Pending';
    } else if (status == 'rejected') {
      color = AppColors.ageRejected;
      icon = Icons.cancel;
      label = 'Verification Rejected';
    } else {
      color = AppColors.textHint;
      icon = Icons.error_outline;
      label = 'Not Verified';
    }

    return Tooltip(
      message: label,
      child: Icon(icon, color: color, size: size),
    );
  }
}

class AgeVerificationStatusCard extends StatelessWidget {
  final String? status;

  const AgeVerificationStatusCard({super.key, this.status});

  @override
  Widget build(BuildContext context) {
    Color color;
    IconData icon;
    String title;
    String message;

    switch (status) {
      case 'approved':
        color = AppColors.ageVerified;
        icon = Icons.verified;
        title = 'Age Verified';
        message = 'Your age has been verified successfully. You can order age-restricted products.';
        break;
      case 'pending':
        color = AppColors.agePending;
        icon = Icons.access_time;
        title = 'Pending Review';
        message = 'Your verification documents are being reviewed. This usually takes 24-48 hours.';
        break;
      case 'rejected':
        color = AppColors.ageRejected;
        icon = Icons.cancel;
        title = 'Verification Rejected';
        message = 'Your verification was rejected. Please submit new documents.';
        break;
      default:
        color = AppColors.textHint;
        icon = Icons.error_outline;
        title = 'Not Verified';
        message = 'Please verify your age to order alcoholic products.';
    }

    return Card(
      color: color.withAlpha(12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            Icon(icon, color: color, size: 32),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title,
                      style: TextStyle(
                          fontWeight: FontWeight.bold, color: color)),
                  const SizedBox(height: 4),
                  Text(message,
                      style: TextStyle(
                          fontSize: 12, color: color.withAlpha(179))),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
