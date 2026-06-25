import 'package:flutter/material.dart';
import 'package:shared_core/shared_core.dart';

class RiderDeliveryProvider extends ChangeNotifier {
  final ApiClient _apiClient;
  List<RiderDelivery> _deliveries = [];
  List<RiderDelivery> _activeDeliveries = [];
  RiderDelivery? _currentDelivery;
  bool _isLoading = false;
  String? _error;

  RiderDeliveryProvider({required ApiClient apiClient}) : _apiClient = apiClient;

  List<RiderDelivery> get deliveries => _deliveries;
  List<RiderDelivery> get activeDeliveries => _activeDeliveries;
  RiderDelivery? get currentDelivery => _currentDelivery;
  bool get isLoading => _isLoading;
  String? get error => _error;

  Future<void> fetchDeliveries() async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final response = await _apiClient.get(Endpoints.riderDeliveries);
      final list = (response['deliveries'] as List?) ?? [];
      _deliveries = list.map((d) => RiderDelivery.fromJson(d)).toList();
      _isLoading = false;
      notifyListeners();
    } on ApiException catch (e) {
      _error = e.message;
      _isLoading = false;
      notifyListeners();
    } catch (e) {
      _error = 'Failed to load deliveries.';
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> fetchActiveDeliveries() async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final response = await _apiClient.get(
        '${Endpoints.riderDeliveries}?status=accepted,picked_up,en_route,age_verified,payment_successful',
      );
      final list = (response['deliveries'] as List?) ?? [];
      _activeDeliveries = list.map((d) => RiderDelivery.fromJson(d)).toList();
      _isLoading = false;
      notifyListeners();
    } on ApiException catch (e) {
      _error = e.message;
      _isLoading = false;
      notifyListeners();
    } catch (e) {
      _error = 'Failed to load active deliveries.';
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<bool> acceptDelivery(int id) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final response = await _apiClient.post(
        Endpoints.riderAcceptDelivery(id),
      );
      _currentDelivery = RiderDelivery.fromJson(response['delivery']);
      _isLoading = false;
      notifyListeners();
      return true;
    } on ApiException catch (e) {
      _error = e.message;
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  Future<bool> pickupDelivery(int id, {String? photo}) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final body = <String, dynamic>{};
      if (photo != null) body['photo'] = photo;
      final response = await _apiClient.post(
        Endpoints.riderPickupDelivery(id),
        body: body,
      );
      _currentDelivery = RiderDelivery.fromJson(response['delivery']);
      _isLoading = false;
      notifyListeners();
      return true;
    } on ApiException catch (e) {
      _error = e.message;
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  Future<bool> completeDelivery(int id) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final response = await _apiClient.post(
        Endpoints.riderCompleteDelivery(id),
      );
      _currentDelivery = RiderDelivery.fromJson(response['delivery']);
      await fetchDeliveries();
      await fetchActiveDeliveries();
      _isLoading = false;
      notifyListeners();
      return true;
    } on ApiException catch (e) {
      _error = e.message;
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  Future<void> updateDeliveryStatus(int id, String status) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final response = await _apiClient.put(
        Endpoints.riderDeliveryDetail(id),
        body: {'status': status},
      );
      _currentDelivery = RiderDelivery.fromJson(response['delivery']);
      await fetchDeliveries();
      await fetchActiveDeliveries();
      _isLoading = false;
      notifyListeners();
    } on ApiException catch (e) {
      _error = e.message;
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<bool> verifyAge(int deliveryId, {required String documentType, required String documentNumber}) async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    try {
      await _apiClient.post(
        Endpoints.mobileDeliveryVerifyAge,
        body: {
          'order_id': deliveryId,
          'document_type': documentType,
          'document_number': documentNumber,
        },
      );
      _isLoading = false;
      notifyListeners();
      return true;
    } on ApiException catch (e) {
      _error = e.message;
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  Future<Map<String, dynamic>?> initiatePayment(int orderId, {required String customerPhone, required double amount}) async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    try {
      final response = await _apiClient.post(
        Endpoints.mobileDeliveryPayment,
        body: {
          'order_id': orderId,
          'customer_phone': customerPhone,
          'amount': amount,
        },
      );
      _isLoading = false;
      notifyListeners();
      return response is Map<String, dynamic> ? response : null;
    } on ApiException catch (e) {
      _error = e.message;
      _isLoading = false;
      notifyListeners();
      return null;
    }
  }

  Future<Map<String, dynamic>?> retryPayment(int paymentId) async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    try {
      final response = await _apiClient.post(
        Endpoints.mobileDeliveryPaymentRetry(paymentId),
      );
      _isLoading = false;
      notifyListeners();
      return response is Map<String, dynamic> ? response : null;
    } on ApiException catch (e) {
      _error = e.message;
      _isLoading = false;
      notifyListeners();
      return null;
    }
  }

  void clearError() {
    _error = null;
    notifyListeners();
  }
}
