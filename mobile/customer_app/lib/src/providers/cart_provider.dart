import 'package:flutter/material.dart';
import 'package:shared_core/shared_core.dart';

class CartProvider extends ChangeNotifier {
  final ApiClient _apiClient;
  List<CartItem> _items = [];
  bool _isLoading = false;
  String? _error;

  CartProvider({required ApiClient apiClient}) : _apiClient = apiClient;

  List<CartItem> get items => _items;
  bool get isLoading => _isLoading;
  String? get error => _error;

  int get itemCount => _items.fold(0, (sum, item) => sum + item.quantity);

  double get subtotal =>
      _items.fold(0.0, (sum, item) => sum + item.subtotal);

  bool get isEmpty => _items.isEmpty;

  Future<void> loadCart() async {
    _isLoading = true;
    notifyListeners();
    try {
      final response = await _apiClient.get(Endpoints.cart);
      _items = (response['items'] as List?)
              ?.map((i) => CartItem.fromJson(i))
              .toList() ??
          [];
      _error = null;
    } on ApiException catch (e) {
      _error = e.message;
    } catch (_) {
      _error = 'Failed to load cart';
    }
    _isLoading = false;
    notifyListeners();
  }

  Future<void> addItem(Product product, {int quantity = 1}) async {
    try {
      await _apiClient.post(
        Endpoints.cart,
        body: {'product_id': product.id, 'quantity': quantity},
      );
      await loadCart();
    } on ApiException catch (e) {
      _error = e.message;
      notifyListeners();
    }
  }

  Future<void> updateQuantity(int productId, int quantity) async {
    if (quantity <= 0) {
      await removeItem(productId);
      return;
    }
    try {
      await _apiClient.put(
        Endpoints.cart,
        body: {'product_id': productId, 'quantity': quantity},
      );
      await loadCart();
    } on ApiException catch (e) {
      _error = e.message;
      notifyListeners();
    }
  }

  Future<void> removeItem(int productId) async {
    try {
      await _apiClient.post(
        '${Endpoints.cart}/remove',
        body: {'product_id': productId},
      );
      await loadCart();
    } on ApiException catch (e) {
      _error = e.message;
      notifyListeners();
    }
  }

  Future<void> clearCart() async {
    try {
      await _apiClient.delete(Endpoints.cart);
      _items = [];
      notifyListeners();
    } on ApiException catch (e) {
      _error = e.message;
      notifyListeners();
    }
  }

  bool hasAgeRestrictedItems() {
    return _items.any((item) => item.requiresAgeVerification);
  }
}
