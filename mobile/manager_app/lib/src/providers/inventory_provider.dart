import 'package:flutter/foundation.dart';
import 'package:shared_core/shared_core.dart';

class InventoryProvider extends ChangeNotifier {
  final ApiClient _api;

  List<Map<String, dynamic>> _stockItems = [];
  bool _isLoading = false;
  String? _error;
  int _lowStockCount = 0;

  InventoryProvider({required ApiClient api}) : _api = api;

  List<Map<String, dynamic>> get stockItems => _stockItems;
  bool get isLoading => _isLoading;
  String? get error => _error;
  int get lowStockCount => _lowStockCount;

  Future<void> fetchInventory() async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    try {
      final response = await _api.get(Endpoints.products);
      final items = response['results'] as List<dynamic>? ?? response as List<dynamic>? ?? [];
      _stockItems = items.cast<Map<String, dynamic>>();
      _lowStockCount = _stockItems.where((item) {
        final stock = item['stock_quantity'] as int? ?? 0;
        final reorder = item['reorder_level'] as int? ?? 0;
        return stock <= reorder;
      }).length;
    } on ApiException catch (e) {
      _error = e.message;
    } on NetworkException {
      _error = 'No internet connection';
    } catch (_) {
      _error = 'Failed to load inventory';
    }
    _isLoading = false;
    notifyListeners();
  }

  Future<void> searchInventory(String query) async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    try {
      final response = await _api.get(
        Endpoints.products,
        queryParams: {'search': query},
      );
      final items = response['results'] as List<dynamic>? ?? response as List<dynamic>? ?? [];
      _stockItems = items.cast<Map<String, dynamic>>();
    } on ApiException catch (e) {
      _error = e.message;
    } on NetworkException {
      _error = 'No internet connection';
    } catch (_) {
      _error = 'Search failed';
    }
    _isLoading = false;
    notifyListeners();
  }

  Future<bool> adjustStock(int itemId, int quantity, String reason) async {
    try {
      await _api.post(
        '${Endpoints.products}/$itemId/adjust-stock',
        body: {'quantity': quantity, 'reason': reason},
      );
      await fetchInventory();
      return true;
    } on ApiException catch (e) {
      _error = e.message;
      notifyListeners();
      return false;
    } on NetworkException {
      _error = 'No internet connection';
      notifyListeners();
      return false;
    } catch (_) {
      _error = 'Stock adjustment failed';
      notifyListeners();
      return false;
    }
  }
}
