import 'package:flutter/material.dart';
import 'package:shared_core/shared_core.dart';

class RiderAuthProvider extends ChangeNotifier {
  final ApiClient _apiClient;
  final TokenStorage _tokenStorage;
  Rider? _user;
  bool _isLoading = true;
  bool _isBiometricEnabled = false;
  bool _isLoggedIn = false;
  String? _error;

  RiderAuthProvider({
    required ApiClient apiClient,
    required TokenStorage tokenStorage,
  })  : _apiClient = apiClient,
        _tokenStorage = tokenStorage {
    checkAuth();
  }

  Rider? get user => _user;
  bool get isLoading => _isLoading;
  bool get isBiometricEnabled => _isBiometricEnabled;
  bool get isLoggedIn => _isLoggedIn;
  String? get error => _error;

  Future<String?> get token => _tokenStorage.getAccessToken();

  Future<void> checkAuth() async {
    try {
      _isLoggedIn = await _tokenStorage.isLoggedIn();
      if (_isLoggedIn) {
        final response = await _apiClient.get(Endpoints.mobileRiderDashboard);
        if (response['rider'] != null) {
          _user = Rider.fromJson(response['rider']);
        }
      }
    } catch (_) {
      _isLoggedIn = false;
      _user = null;
    }
    _isBiometricEnabled = await _tokenStorage.isBiometricEnabled();
    _isLoading = false;
    notifyListeners();
  }

  Future<bool> login(String email, String password) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final response = await _apiClient.post(
        Endpoints.login,
        body: {'email': email, 'password': password},
        auth: false,
      );
      await _tokenStorage.saveTokens(
        accessToken: response['access_token'],
        refreshToken: response['refresh_token'],
      );
      if (response['user'] != null) {
        _user = Rider.fromJson(response['user']);
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
    } catch (e) {
      _error = 'Login failed. Please try again.';
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  Future<bool> loginWithBiometrics() async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final token = await _tokenStorage.getAccessToken();
      if (token == null) {
        _error = 'No saved session found.';
        _isLoading = false;
        notifyListeners();
        return false;
      }
      final response = await _apiClient.get(Endpoints.mobileRiderDashboard);
      if (response['rider'] != null) {
        _user = Rider.fromJson(response['rider']);
      }
      _isLoggedIn = true;
      _isLoading = false;
      notifyListeners();
      return true;
    } catch (e) {
      _error = 'Biometric login failed.';
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  Future<void> logout() async {
    await _tokenStorage.clearTokens();
    _user = null;
    _isLoggedIn = false;
    _error = null;
    notifyListeners();
  }

  Future<void> setBiometricEnabled(bool enabled) async {
    _isBiometricEnabled = enabled;
    await _tokenStorage.setBiometricEnabled(enabled);
    notifyListeners();
  }

  void clearError() {
    _error = null;
    notifyListeners();
  }
}
