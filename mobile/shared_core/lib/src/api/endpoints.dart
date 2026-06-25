class Endpoints {
  static const String baseUrl = 'http://localhost:8000/api/v1';

  static const String login = '/auth/login';
  static const String register = '/auth/register';
  static const String refreshToken = '/auth/refresh';
  static const String verifyPhone = '/auth/verify-phone';
  static const String forgotPassword = '/auth/forgot-password';
  static const String resetPassword = '/auth/reset-password';
  static const String changePassword = '/auth/change-password';

  static const String products = '/products';
  static const String productCategories = '/products/categories';
  static String productDetail(int id) => '/products/$id';
  static const String promotions = '/promotions';

  static const String cart = '/cart';
  static const String checkout = '/checkout';

  static const String orders = '/orders';
  static String orderDetail(int id) => '/orders/$id';
  static String orderTracking(int id) => '/orders/$id/tracking';

  static const String payments = '/payments';
  static const String mpesaStkPush = '/payments/mpesa/stk-push';
  static const String mpesaCallback = '/payments/mpesa/callback';

  static const String delivery = '/delivery';
  static const String deliveryEstimate = '/delivery/estimate';

  static const String loyalty = '/loyalty';
  static const String loyaltyRedeem = '/loyalty/redeem';
  static const String loyaltyHistory = '/loyalty/history';

  static const String customerProfile = '/customers/me';
  static const String customerAddresses = '/customers/addresses';

  static const String verification = '/customers/verification';
  static const String verificationStatus = '/customers/verification/status';

  static const String notifications = '/notifications';
  static String notificationRead(int id) => '/notifications/$id/read';

  static const String riderDeliveries = '/rider/deliveries';
  static String riderDeliveryDetail(int id) => '/rider/deliveries/$id';
  static String riderAcceptDelivery(int id) => '/rider/deliveries/$id/accept';
  static String riderPickupDelivery(int id) => '/rider/deliveries/$id/pickup';
  static String riderCompleteDelivery(int id) => '/rider/deliveries/$id/complete';
  static String riderDeliveryVerification(int id) => '/rider/deliveries/$id/verify';

  static const String mobileDevices = '/mobile/devices';
  static const String mobileRegisterDevice = '/mobile/devices/register';
  static const String mobileUnregisterDevice = '/mobile/devices/unregister';
  static const String mobilePreferences = '/mobile/preferences';
  static const String mobileSessions = '/mobile/sessions';
  static String mobileEndSession(String token) => '/mobile/sessions/$token/end';
  static const String mobileCustomerDashboard = '/mobile/dashboard/customer';
  static const String mobileRiderDashboard = '/mobile/dashboard/rider';
  static const String mobileManagerDashboard = '/mobile/dashboard/manager';
  static const String mobileExecutiveDashboard = '/mobile/dashboard/executive';
  static const String mobileLocationUpdate = '/mobile/location/update';
  static const String mobileActiveRiders = '/mobile/location/riders';
  static const String mobileNearbyRiders = '/mobile/location/nearby';
  static const String mobileLocationHistory = '/mobile/location/history';
  static const String mobileIncidents = '/mobile/incidents';
  static String mobileIncidentResolve(int id) => '/mobile/incidents/$id/resolve';
  static const String mobileNotifications = '/mobile/notifications';
  static String mobileNotificationRead(int id) => '/mobile/notifications/$id/read';
  static const String mobileSendNotification = '/mobile/notifications/send';

  static String get mobileDeliveryVerifyAge => '/mobile/delivery/verify-age';
  static String mobileDeliveryVerification(int orderId) => '/mobile/delivery/verification/$orderId';
  static String get mobileDeliveryPayment => '/mobile/delivery/payment';
  static String mobileDeliveryPaymentRetry(int paymentId) => '/mobile/delivery/payment/$paymentId/retry';
  static String mobileDeliveryPaymentDetail(int orderId) => '/mobile/delivery/payment/$orderId';
}
