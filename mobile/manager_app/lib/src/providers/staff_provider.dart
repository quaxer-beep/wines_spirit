import 'package:flutter/foundation.dart';
import 'package:shared_core/shared_core.dart';

class StaffProvider extends ChangeNotifier {
  final ApiClient _api;

  List<Map<String, dynamic>> _staff = [];
  bool _isLoading = false;
  String? _error;

  StaffProvider({required ApiClient api}) : _api = api;

  List<Map<String, dynamic>> get staff => _staff;
  bool get isLoading => _isLoading;
  String? get error => _error;

  Future<void> fetchStaff() async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    try {
      final response = await _api.get('/staff');
      final items = response['results'] as List<dynamic>? ?? response as List<dynamic>? ?? [];
      _staff = items.cast<Map<String, dynamic>>();
    } on ApiException catch (e) {
      _error = e.message;
    } on NetworkException {
      _error = 'No internet connection';
    } catch (_) {
      _error = 'Failed to load staff';
    }
    _isLoading = false;
    notifyListeners();
  }

  Future<Map<String, dynamic>?> getStaffPerformance(int id) async {
    try {
      final response = await _api.get('/staff/$id/performance');
      return response as Map<String, dynamic>;
    } on ApiException catch (e) {
      _error = e.message;
      notifyListeners();
      return null;
    } on NetworkException {
      _error = 'No internet connection';
      notifyListeners();
      return null;
    } catch (_) {
      _error = 'Failed to load staff performance';
      notifyListeners();
      return null;
    }
  }
}
