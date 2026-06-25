import 'package:flutter/foundation.dart';
import 'package:shared_core/shared_core.dart';

class ExecDashboardProvider extends ChangeNotifier {
  final ApiClient _apiClient;

  ExecDashboardProvider({required ApiClient apiClient}) : _apiClient = apiClient;

  double _totalRevenue = 0;
  double _totalProfit = 0;
  double _totalInventoryValue = 0;
  double _revenueGrowth = 0;
  double _profitGrowth = 0;
  int _totalOrders = 0;
  int _totalBranches = 0;
  bool _isLoading = false;
  String? _error;

  double get totalRevenue => _totalRevenue;
  double get totalProfit => _totalProfit;
  double get totalInventoryValue => _totalInventoryValue;
  double get revenueGrowth => _revenueGrowth;
  double get profitGrowth => _profitGrowth;
  int get totalOrders => _totalOrders;
  int get totalBranches => _totalBranches;
  bool get isLoading => _isLoading;
  String? get error => _error;

  Future<void> fetchDashboard(String period) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final response = await _apiClient.get(
        Endpoints.execDashboard,
        queryParams: {'period': period},
      );
      _totalRevenue = (response['total_revenue'] ?? 0).toDouble();
      _totalProfit = (response['total_profit'] ?? 0).toDouble();
      _totalInventoryValue = (response['total_inventory_value'] ?? 0).toDouble();
      _revenueGrowth = (response['revenue_growth'] ?? 0).toDouble();
      _profitGrowth = (response['profit_growth'] ?? 0).toDouble();
      _totalOrders = response['total_orders'] ?? 0;
      _totalBranches = response['total_branches'] ?? 0;
    } catch (e) {
      _error = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }
}
