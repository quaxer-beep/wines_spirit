import 'package:intl/intl.dart';

class Formatters {
  Formatters._();

  static String formatCurrency(double amount) {
    final formatter = NumberFormat('#,##0', 'en-KE');
    return 'KSh ${formatter.format(amount)}';
  }

  static String formatDate(String? dateStr) {
    if (dateStr == null) return '';
    try {
      final date = DateTime.parse(dateStr);
      return DateFormat('MMM dd, yyyy').format(date);
    } catch (_) {
      return dateStr;
    }
  }

  static String formatDateTime(String? dateStr) {
    if (dateStr == null) return '';
    try {
      final date = DateTime.parse(dateStr);
      return DateFormat('MMM dd, yyyy HH:mm').format(date);
    } catch (_) {
      return dateStr;
    }
  }

  static String formatTime(String? dateStr) {
    if (dateStr == null) return '';
    try {
      final date = DateTime.parse(dateStr);
      return DateFormat('HH:mm').format(date);
    } catch (_) {
      return dateStr;
    }
  }

  static String timeAgo(String? dateStr) {
    if (dateStr == null) return '';
    try {
      final date = DateTime.parse(dateStr);
      final now = DateTime.now();
      final diff = now.difference(date);

      if (diff.inDays > 365) {
        return '${(diff.inDays / 365).floor()}y ago';
      }
      if (diff.inDays > 30) {
        return '${(diff.inDays / 30).floor()}mo ago';
      }
      if (diff.inDays > 0) {
        return '${diff.inDays}d ago';
      }
      if (diff.inHours > 0) {
        return '${diff.inHours}h ago';
      }
      if (diff.inMinutes > 0) {
        return '${diff.inMinutes}m ago';
      }
      return 'Just now';
    } catch (_) {
      return dateStr;
    }
  }

  static String formatPhone(String phone) {
    if (phone.startsWith('254')) {
      return '0${phone.substring(3)}';
    }
    if (phone.startsWith('+254')) {
      return '0${phone.substring(4)}';
    }
    return phone;
  }

  static String formatPoints(int points) {
    return NumberFormat('#,##0').format(points);
  }

  static String formatPercentage(double value) {
    return '${value.toStringAsFixed(1)}%';
  }

  static String formatDistance(double km) {
    if (km < 1) {
      return '${(km * 1000).toInt()}m';
    }
    return '${km.toStringAsFixed(1)}km';
  }

  static String maskPhone(String phone) {
    if (phone.length < 8) return phone;
    return '${phone.substring(0, 4)}****${phone.substring(phone.length - 2)}';
  }
}
