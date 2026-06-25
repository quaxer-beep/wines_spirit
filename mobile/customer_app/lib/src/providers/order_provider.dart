import 'package:flutter/material.dart';
import 'package:shared_core/shared_core.dart';

class OrderProvider extends ChangeNotifier {
  final ApiClient _apiClient;
  List<Order> _orders = [];
  Order? _currentOrder;
  bool _isLoading = false;
  String? _error;

  OrderProvider({required ApiClient apiClient}) : _apiClient = apiClient;

  List<Order> get orders => _orders;
  Order? get currentOrder => _currentOrder;
  bool get isLoading => _isLoading;
  String? get error => _error;

  Future<void> loadOrders({int page = 1}) async {
    _isLoading = true;
    notifyListeners();
    try {
      final response = await _apiClient.get(
        Endpoints.orders,
        queryParams: {'page': page.toString(), 'page_size': '20'},
      );
      _orders = (response['items'] as List?)
              ?.map((o) => Order.fromJson(o))
              .toList() ??
          [];
      _error = null;
    } on ApiException catch (e) {
      _error = e.message;
    } catch (_) {
      _error = 'Failed to load orders';
    }
    _isLoading = false;
    notifyListeners();
  }

  Future<void> loadOrderDetail(int orderId) async {
    _isLoading = true;
    notifyListeners();
    try {
      final response = await _apiClient.get(Endpoints.orderDetail(orderId));
      _currentOrder = Order.fromJson(response);
      _error = null;
    } on ApiException catch (e) {
      _error = e.message;
    } catch (_) {
      _error = 'Failed to load order details';
    }
    _isLoading = false;
    notifyListeners();
  }

  Future<Order?> placeOrder({
    required int addressId,
    required double deliveryFee,
    int? loyaltyPoints,
  }) async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    try {
      final response = await _apiClient.post(
        Endpoints.checkout,
        body: {
          'address_id': addressId,
          'delivery_fee': deliveryFee,
          if (loyaltyPoints != null) 'loyalty_points': loyaltyPoints,
        },
      );
      final order = Order.fromJson(response);
      _currentOrder = order;
      _error = null;
      _isLoading = false;
      notifyListeners();
      return order;
    } on ApiException catch (e) {
      _error = e.message;
      _isLoading = false;
      notifyListeners();
      return null;
    } catch (e) {
      _error = 'Failed to place order';
      _isLoading = false;
      notifyListeners();
      return null;
    }
  }

  Future<bool> initiatePayment(int orderId, String phone) async {
    try {
      await _apiClient.post(
        Endpoints.mpesaStkPush,
        body: {'order_id': orderId, 'phone': phone},
      );
      return true;
    } on ApiException catch (e) {
      _error = e.message;
      notifyListeners();
      return false;
    }
  }

  void clearError() {
    _error = null;
    notifyListeners();
  }
}
