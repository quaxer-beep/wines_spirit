import 'package:flutter/material.dart';
import 'package:shared_core/shared_core.dart';

class AuthProvider extends ChangeNotifier {
  final AuthService _authService;
  Customer? _user;
  bool _isLoading = true;
  bool _isAuthenticated = false;
  String? _error;

  AuthProvider({required AuthService authService})
      : _authService = authService {
    _checkAuth();
  }

  Customer? get user => _user;
  bool get isLoading => _isLoading;
  bool get isAuthenticated => _isAuthenticated;
  String? get error => _error;

  Future<void> _checkAuth() async {
    try {
      _isAuthenticated = await _authService.isLoggedIn();
      if (_isAuthenticated) {
        _user = await _authService.getProfile();
      }
    } catch (_) {
      _isAuthenticated = false;
    }
    _isLoading = false;
    notifyListeners();
  }

  Future<bool> login(String phone, String password) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final result = await _authService.login(phone, password);
      _user = result.user;
      _isAuthenticated = true;
      _isLoading = false;
      notifyListeners();
      return true;
    } on ApiException catch (e) {
      _error = e.message;
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

  Future<bool> register({
    required String fullName,
    required String phone,
    required String password,
    String? email,
    DateTime? dateOfBirth,
  }) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final result = await _authService.register(
        fullName: fullName,
        phone: phone,
        password: password,
        email: email,
        dateOfBirth: dateOfBirth,
      );
      _user = result.user;
      _isAuthenticated = true;
      _isLoading = false;
      notifyListeners();
      return true;
    } on ApiException catch (e) {
      _error = e.message;
      _isLoading = false;
      notifyListeners();
      return false;
    } catch (e) {
      _error = 'Registration failed. Please try again.';
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  Future<void> logout() async {
    await _authService.logout();
    _user = null;
    _isAuthenticated = false;
    _error = null;
    notifyListeners();
  }

  Future<bool> isBiometricEnabled() => _authService.isBiometricEnabled();

  Future<void> setBiometricEnabled(bool enabled) async {
    await _authService.setBiometricEnabled(enabled);
    notifyListeners();
  }

  void clearError() {
    _error = null;
    notifyListeners();
  }
}
