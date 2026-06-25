import 'package:flutter/foundation.dart';
import 'package:shared_core/shared_core.dart';

class SalesProvider extends ChangeNotifier {
  final ApiClient _api;

  List<Map<String, dynamic>> _todaySales = [];
  double _totalRevenue = 0;
  int _transactionCount = 0;
  List<Map<String, dynamic>> _topProducts = [];
  bool _isLoading = false;
  String? _error;

  SalesProvider({required ApiClient api}) : _api = api;

  List<Map<String, dynamic>> get todaySales => _todaySales;
  double get totalRevenue => _totalRevenue;
  int get transactionCount => _transactionCount;
  List<Map<String, dynamic>> get topProducts => _topProducts;
  bool get isLoading => _isLoading;
  String? get error => _error;

  Future<void> fetchSales() async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    try {
      final response = await _api.get(Endpoints.mobileManagerDashboard);
      _todaySales = (response['recent_transactions'] as List<dynamic>?)
              ?.cast<Map<String, dynamic>>() ??
          [];
      _totalRevenue = (response['today_sales'] as num?)?.toDouble() ?? 0;
      _transactionCount = response['today_orders'] as int? ?? 0;
      _topProducts = (response['top_products'] as List<dynamic>?)
              ?.cast<Map<String, dynamic>>() ??
          [];
    } on ApiException catch (e) {
      _error = e.message;
    } on NetworkException {
      _error = 'No internet connection';
    } catch (_) {
      _error = 'Failed to load sales';
    }
    _isLoading = false;
    notifyListeners();
  }

  Future<void> fetchSalesByDateRange(DateTime start, DateTime end) async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    try {
      final response = await _api.get(
        Endpoints.orders,
        queryParams: {
          'start_date': start.toIso8601String().split('T')[0],
          'end_date': end.toIso8601String().split('T')[0],
        },
      );
      final orders = response['results'] as List<dynamic>? ?? response as List<dynamic>? ?? [];
      _todaySales = orders.cast<Map<String, dynamic>>();
      _totalRevenue = _todaySales.fold<double>(
          0, (sum, o) => sum + ((o['total_amount'] as num?)?.toDouble() ?? 0));
      _transactionCount = _todaySales.length;
    } on ApiException catch (e) {
      _error = e.message;
    } on NetworkException {
      _error = 'No internet connection';
    } catch (_) {
      _error = 'Failed to load sales';
    }
    _isLoading = false;
    notifyListeners();
  }
}
