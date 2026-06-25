class MobileDevice {
  final int id;
  final String deviceToken;
  final String platform;
  final String? deviceModel;
  final String? osVersion;
  final String? appVersion;
  final bool isActive;
  final String? lastSeenAt;

  MobileDevice({
    required this.id,
    required this.deviceToken,
    required this.platform,
    this.deviceModel,
    this.osVersion,
    this.appVersion,
    this.isActive = true,
    this.lastSeenAt,
  });

  factory MobileDevice.fromJson(Map<String, dynamic> json) {
    return MobileDevice(
      id: json['id'],
      deviceToken: json['device_token'] ?? '',
      platform: json['platform'] ?? '',
      deviceModel: json['device_model'],
      osVersion: json['os_version'],
      appVersion: json['app_version'],
      isActive: json['is_active'] ?? true,
      lastSeenAt: json['last_seen_at'],
    );
  }
}

class AppPreferences {
  final String theme;
  final String language;
  final bool notificationsEnabled;
  final bool locationTrackingEnabled;
  final bool biometricEnabled;

  AppPreferences({
    this.theme = 'light',
    this.language = 'en',
    this.notificationsEnabled = true,
    this.locationTrackingEnabled = true,
    this.biometricEnabled = false,
  });

  factory AppPreferences.fromJson(Map<String, dynamic> json) {
    return AppPreferences(
      theme: json['theme'] ?? 'light',
      language: json['language'] ?? 'en',
      notificationsEnabled: json['notifications_enabled'] ?? true,
      locationTrackingEnabled: json['location_tracking_enabled'] ?? true,
      biometricEnabled: json['biometric_enabled'] ?? false,
    );
  }

  Map<String, dynamic> toJson() => {
        'theme': theme,
        'language': language,
        'notifications_enabled': notificationsEnabled,
        'location_tracking_enabled': locationTrackingEnabled,
        'biometric_enabled': biometricEnabled,
      };

  bool get isDarkMode => theme == 'dark';
}
