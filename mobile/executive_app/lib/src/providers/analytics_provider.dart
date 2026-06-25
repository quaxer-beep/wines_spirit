import 'package:flutter/foundation.dart';
import 'package:shared_core/shared_core.dart';

class AnalyticsProvider extends ChangeNotifier {
  final ApiClient _apiClient;

  AnalyticsProvider({required ApiClient apiClient}) : _apiClient = apiClient;

  List<Map<String, dynamic>> _revenueByBranch = [];
  List<Map<String, dynamic>> _revenueByBrand = [];
  List<Map<String, dynamic>> _revenueByCategory = [];
  List<Map<String, dynamic>> _kpiTrends = [];
  bool _isLoading = false;

  List<Map<String, dynamic>> get revenueByBranch => _revenueByBranch;
  List<Map<String, dynamic>> get revenueByBrand => _revenueByBrand;
  List<Map<String, dynamic>> get revenueByCategory => _revenueByCategory;
  List<Map<String, dynamic>> get kpiTrends => _kpiTrends;
  bool get isLoading => _isLoading;

  Future<void> fetchRevenueByBranch() async {
    _isLoading = true;
    notifyListeners();

    try {
      final response = await _apiClient.get(Endpoints.execAnalyticsRevenueByBranch);
      _revenueByBranch = List<Map<String, dynamic>>.from(response['data'] ?? []);
    } catch (_) {
      _revenueByBranch = [];
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> fetchRevenueByBrand() async {
    _isLoading = true;
    notifyListeners();

    try {
      final response = await _apiClient.get(Endpoints.execAnalyticsRevenueByBrand);
      _revenueByBrand = List<Map<String, dynamic>>.from(response['data'] ?? []);
    } catch (_) {
      _revenueByBrand = [];
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> fetchRevenueByCategory() async {
    _isLoading = true;
    notifyListeners();

    try {
      final response = await _apiClient.get(Endpoints.execAnalyticsRevenueByCategory);
      _revenueByCategory = List<Map<String, dynamic>>.from(response['data'] ?? []);
    } catch (_) {
      _revenueByCategory = [];
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> fetchKpiTrends(String period) async {
    _isLoading = true;
    notifyListeners();

    try {
      final response = await _apiClient.get(
        Endpoints.execAnalyticsKpiTrends,
        queryParams: {'period': period},
      );
      _kpiTrends = List<Map<String, dynamic>>.from(response['data'] ?? []);
    } catch (_) {
      _kpiTrends = [];
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }
}
