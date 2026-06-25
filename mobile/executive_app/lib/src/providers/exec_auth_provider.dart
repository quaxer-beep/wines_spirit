import 'package:flutter/foundation.dart';
import 'package:shared_core/shared_core.dart';

class ExecAuthProvider extends ChangeNotifier {
  final ApiClient _apiClient;

  ExecAuthProvider({required ApiClient apiClient}) : _apiClient = apiClient;

  bool _isLoading = false;
  bool _isLoggedIn = false;
  Map<String, dynamic>? _user;
  List<Map<String, dynamic>> _accessibleBranches = [];

  bool get isLoading => _isLoading;
  bool get isLoggedIn => _isLoggedIn;
  Map<String, dynamic>? get user => _user;
  List<Map<String, dynamic>> get accessibleBranches => _accessibleBranches;

  Future<void> checkAuth() async {
    _isLoading = true;
    notifyListeners();

    try {
      final response = await _apiClient.get(Endpoints.execAuthCheck);
      _isLoggedIn = response['is_logged_in'] ?? false;
      _user = response['user'];
      _accessibleBranches = List<Map<String, dynamic>>.from(
        response['accessible_branches'] ?? [],
      );
    } catch (_) {
      _isLoggedIn = false;
      _user = null;
      _accessibleBranches = [];
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<bool> login(String email, String password) async {
    _isLoading = true;
    notifyListeners();

    try {
      final response = await _apiClient.post(
        Endpoints.execLogin,
        body: {'email': email, 'password': password},
        auth: false,
      );
      _isLoggedIn = true;
      _user = response['user'];
      _accessibleBranches = List<Map<String, dynamic>>.from(
        response['accessible_branches'] ?? [],
      );
      _isLoading = false;
      notifyListeners();
      return true;
    } catch (_) {
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  Future<void> logout() async {
    _isLoading = true;
    notifyListeners();

    try {
      await _apiClient.post(Endpoints.execLogout);
    } catch (_) {}

    _isLoggedIn = false;
    _user = null;
    _accessibleBranches = [];
    _isLoading = false;
    notifyListeners();
  }
}
