import 'package:flutter/foundation.dart';
import 'package:shared_core/shared_core.dart';

class ApprovalProvider extends ChangeNotifier {
  final ApiClient _api;

  List<Map<String, dynamic>> _pendingApprovals = [];
  List<Map<String, dynamic>> _approvedApprovals = [];
  List<Map<String, dynamic>> _rejectedApprovals = [];
  bool _isLoading = false;
  String? _error;

  ApprovalProvider({required ApiClient api}) : _api = api;

  List<Map<String, dynamic>> get pendingApprovals => _pendingApprovals;
  List<Map<String, dynamic>> get approvedApprovals => _approvedApprovals;
  List<Map<String, dynamic>> get rejectedApprovals => _rejectedApprovals;
  bool get isLoading => _isLoading;
  String? get error => _error;

  Future<void> fetchApprovals() async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    try {
      final response = await _api.get('/approvals');
      final items = response['results'] as List<dynamic>? ?? response as List<dynamic>? ?? [];
      final all = items.cast<Map<String, dynamic>>();
      _pendingApprovals = all.where((a) => a['status'] == 'pending').toList();
      _approvedApprovals = all.where((a) => a['status'] == 'approved').toList();
      _rejectedApprovals = all.where((a) => a['status'] == 'rejected').toList();
    } on ApiException catch (e) {
      _error = e.message;
    } on NetworkException {
      _error = 'No internet connection';
    } catch (_) {
      _error = 'Failed to load approvals';
    }
    _isLoading = false;
    notifyListeners();
  }

  Future<bool> approve(int id, String note) async {
    try {
      await _api.post('/approvals/$id/approve', body: {'note': note});
      await fetchApprovals();
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
      _error = 'Failed to approve';
      notifyListeners();
      return false;
    }
  }

  Future<bool> reject(int id, String reason) async {
    try {
      await _api.post('/approvals/$id/reject', body: {'reason': reason});
      await fetchApprovals();
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
      _error = 'Failed to reject';
      notifyListeners();
      return false;
    }
  }
}
