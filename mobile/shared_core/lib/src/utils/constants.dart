class AppConstants {
  AppConstants._();

  static const String appName = 'Wines & Spirits';
  static const String customerAppName = 'W&S Customer';
  static const String riderAppName = 'W&S Rider';
  static const String managerAppName = 'W&S Manager';
  static const String executiveAppName = 'W&S Executive';

  static const String appVersion = '1.0.0';

  static const int defaultPageSize = 20;
  static const int connectionTimeout = 30;
  static const int locationUpdateInterval = 10;
  static const int maxCartQuantity = 99;

  static const double deliveryBaseFee = 100.0;
  static const double deliveryPerKmRate = 30.0;

  static const int legalDrinkingAge = 18;
  static const String kenyanPhoneRegex = r'^(?:\+?254|0)?[17]\d{8}$';

  static const int minPasswordLength = 6;
  static const int maxPasswordLength = 128;

  static const List<String> productCategories = [
    'Wines',
    'Spirits',
    'Beer',
    'Soft Drinks',
    'Others',
  ];

  static const List<String> deliveryStatuses = [
    'assigned',
    'accepted',
    'picked_up',
    'en_route',
    'delivered',
    'failed',
  ];
}
