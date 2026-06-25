import 'package:flutter/material.dart';

class AppColors {
  AppColors._();

  static const Color primary = Color(0xFF8B1A2B);
  static const Color primaryLight = Color(0xFFA82E3E);
  static const Color primaryDark = Color(0xFF6B0F1E);

  static const Color secondary = Color(0xFFD4A843);
  static const Color secondaryLight = Color(0xFFE8C56A);
  static const Color secondaryDark = Color(0xFFB8912E);

  static const Color accent = Color(0xFF2E7D32);

  static const Color background = Color(0xFFF8F9FA);
  static const Color surface = Color(0xFFFFFFFF);
  static const Color surfaceVariant = Color(0xFFF1F3F5);

  static const Color textPrimary = Color(0xFF1A1A2E);
  static const Color textSecondary = Color(0xFF6C757D);
  static const Color textHint = Color(0xFFADB5BD);
  static const Color textOnPrimary = Color(0xFFFFFFFF);

  static const Color success = Color(0xFF2E7D32);
  static const Color warning = Color(0xFFFFA726);
  static const Color error = Color(0xFFD32F2F);
  static const Color info = Color(0xFF1976D2);

  static const Color border = Color(0xFFDEE2E6);
  static const Color divider = Color(0xFFE9ECEF);

  static const Color ageVerified = Color(0xFF2E7D32);
  static const Color agePending = Color(0xFFFFA726);
  static const Color ageRejected = Color(0xFFD32F2F);

  static const Color darkBackground = Color(0xFF121212);
  static const Color darkSurface = Color(0xFF1E1E1E);
  static const Color darkSurfaceVariant = Color(0xFF2C2C2C);
  static const Color darkTextPrimary = Color(0xFFF5F5F5);
  static const Color darkTextSecondary = Color(0xFFB0B0B0);

  static const Color loyaltyGold = Color(0xFFFFD700);
  static const Color mpesaGreen = Color(0xFF4CAF50);

  static Color statusColor(String status) {
    switch (status.toLowerCase()) {
      case 'pending':
        return warning;
      case 'confirmed':
      case 'paid':
      case 'completed':
      case 'delivered':
        return success;
      case 'cancelled':
      case 'failed':
      case 'rejected':
        return error;
      case 'preparing':
      case 'processing':
        return info;
      case 'out_for_delivery':
      case 'en_route':
      case 'in_transit':
        return const Color(0xFF7B1FA2);
      default:
        return textSecondary;
    }
  }
}
