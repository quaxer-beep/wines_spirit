import 'package:flutter/foundation.dart';
import 'package:shared_core/shared_core.dart';

class BranchProvider extends ChangeNotifier {
  final ApiClient _apiClient;

  BranchProvider({required ApiClient apiClient}) : _apiClient = apiClient;

  List<Map<String, dynamic>> _branchComparisons = [];
  bool _isLoading = false;
  String? _selectedMetric;

  List<Map<String, dynamic>> get branchComparisons => _branchComparisons;
  bool get isLoading => _isLoading;
  String? get selectedMetric => _selectedMetric;

  Future<void> fetchBranchComparisons() async {
    _isLoading = true;
    notifyListeners();

    try {
      final response = await _apiClient.get(Endpoints.execBranchComparisons);
      _branchComparisons = List<Map<String, dynamic>>.from(response['data'] ?? []);
    } catch (_) {
      _branchComparisons = [];
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  void compareByMetric(String metric) {
    _selectedMetric = metric;
    _branchComparisons.sort((a, b) {
      final aVal = (a[metric] ?? 0).toDouble();
      final bVal = (b[metric] ?? 0).toDouble();
      return bVal.compareTo(aVal);
    });
    notifyListeners();
  }
}
