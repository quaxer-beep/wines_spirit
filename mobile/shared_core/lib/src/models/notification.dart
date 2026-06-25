class AppNotification {
  final int id;
  final String notificationType;
  final String title;
  final String message;
  final String? referenceType;
  final int? referenceId;
  final bool isRead;
  final String sentAt;
  final String? readAt;

  AppNotification({
    required this.id,
    required this.notificationType,
    required this.title,
    required this.message,
    this.referenceType,
    this.referenceId,
    this.isRead = false,
    required this.sentAt,
    this.readAt,
  });

  factory AppNotification.fromJson(Map<String, dynamic> json) {
    return AppNotification(
      id: json['id'],
      notificationType: json['notification_type'] ?? '',
      title: json['title'] ?? '',
      message: json['message'] ?? '',
      referenceType: json['reference_type'],
      referenceId: json['reference_id'],
      isRead: json['is_read'] ?? false,
      sentAt: json['sent_at'] ?? json['created_at'] ?? '',
      readAt: json['read_at'],
    );
  }

  String get timeAgo {
    // Simplified - real implementation would parse and format
    return sentAt;
  }
}

class PushNotificationPayload {
  final String title;
  final String body;
  final String? notificationType;
  final Map<String, dynamic>? data;

  PushNotificationPayload({
    required this.title,
    required this.body,
    this.notificationType,
    this.data,
  });
}
