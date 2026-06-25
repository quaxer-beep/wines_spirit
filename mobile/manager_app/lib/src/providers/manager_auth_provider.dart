import 'package:flutter/foundation.dart';
import 'package:shared_core/shared_core.dart';

class ManagerAuthProvider extends ChangeNotifier {
  final ApiClient _api;
  final TokenStorage _tokenStorage;

  bool _isLoading = false;
  bool _isLoggedIn = false;
  Map<String, dynamic>? _user;
  String? _branchName;
  int? _branchId;
  String? _error;

  ManagerAuthProvider({
    required ApiClient api,
    required TokenStorage tokenStorage,
  })  : _api = api,
        _tokenStorage = tokenStorage;

  bool get isLoading => _isLoading;
  bool get isLoggedIn => _isLoggedIn;
  Map<String, dynamic>? get user => _user;
  String? get branchName => _branchName;
  int? get branchId => _branchId;
  String? get error => _error;

  Future<void> checkAuth() async {
    _isLoading = true;
    notifyListeners();
    try {
      _isLoggedIn = await _tokenStorage.isLoggedIn();
      if (_isLoggedIn) {
        final role = await _tokenStorage.getUserRole();
        if (role == 'manager' || role == 'admin') {
          final userId = await _tokenStorage.getUserId();
          if (userId != null) {
            _user = {'id': userId, 'role': role};
          }
        } else {
          _isLoggedIn = false;
          await _tokenStorage.clearTokens();
        }
      }
    } catch (_) {
      _isLoggedIn = false;
    }
    _isLoading = false;
    notifyListeners();
  }

  Future<bool> login(String email, String password) async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    try {
      final response = await _api.post(
        Endpoints.login,
        body: {'email': email, 'password': password},
        auth: false,
      );
      await _tokenStorage.saveTokens(
        accessToken: response['access_token'] as String,
        refreshToken: response['refresh_token'] as String?,
      );
      if (response['user'] != null) {
        _user = response['user'] as Map<String, dynamic>;
        final role = _user?['role'] as String? ?? 'manager';
        final userId = _user?['id'] as int? ?? 0;
        await _tokenStorage.saveUserDetails(role: role, userId: userId);
        _branchName = _user?['branch_name'] as String?;
        _branchId = _user?['branch_id'] as int?;
      }
      _isLoggedIn = true;
      _isLoading = false;
      notifyListeners();
      return true;
    } on ApiException catch (e) {
      _error = e.message;
      _isLoading = false;
      notifyListeners();
      return false;
    } on NetworkException {
      _error = 'No internet connection';
      _isLoading = false;
      notifyListeners();
      return false;
    } catch (e) {
      _error = 'Login failed. Please try again.';
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  Future<void> logout() async {
    _isLoading = true;
    notifyListeners();
    await _tokenStorage.clearTokens();
    _isLoggedIn = false;
    _user = null;
    _branchName = null;
    _branchId = null;
    _error = null;
    _isLoading = false;
    notifyListeners();
  }
}
