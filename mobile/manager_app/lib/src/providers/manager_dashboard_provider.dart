import 'package:flutter/foundation.dart';
import 'package:shared_core/shared_core.dart';

class ManagerDashboardProvider extends ChangeNotifier {
  final ApiClient _api;

  double _todaySales = 0;
  int _todayOrders = 0;
  int _lowStockItems = 0;
  int _pendingApprovals = 0;
  bool _isLoading = false;
  String? _error;

  ManagerDashboardProvider({required ApiClient api}) : _api = api;

  double get todaySales => _todaySales;
  int get todayOrders => _todayOrders;
  int get lowStockItems => _lowStockItems;
  int get pendingApprovals => _pendingApprovals;
  bool get isLoading => _isLoading;
  String? get error => _error;

  Future<void> fetchDashboard() async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    try {
      final response = await _api.get(Endpoints.mobileManagerDashboard);
      _todaySales = (response['today_sales'] as num?)?.toDouble() ?? 0;
      _todayOrders = response['today_orders'] as int? ?? 0;
      _lowStockItems = response['low_stock_count'] as int? ?? 0;
      _pendingApprovals = response['pending_approvals'] as int? ?? 0;
    } on ApiException catch (e) {
      _error = e.message;
    } on NetworkException {
      _error = 'No internet connection';
    } catch (_) {
      _error = 'Failed to load dashboard';
    }
    _isLoading = false;
    notifyListeners();
  }
}
