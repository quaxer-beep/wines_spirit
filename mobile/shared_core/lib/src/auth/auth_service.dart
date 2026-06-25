import '../api/api_client.dart';
import '../api/endpoints.dart';
import '../models/customer.dart';
import 'token_storage.dart';

class AuthService {
  final ApiClient _api;
  final TokenStorage _tokenStorage;

  AuthService({
    required ApiClient api,
    required TokenStorage tokenStorage,
  })  : _api = api,
        _tokenStorage = tokenStorage;

  Future<AuthResult> login(String phone, String password) async {
    final response = await _api.post(
      Endpoints.login,
      body: {'phone': phone, 'password': password},
      auth: false,
    );
    await _saveTokens(response);
    return AuthResult.fromJson(response);
  }

  Future<AuthResult> register({
    required String fullName,
    required String phone,
    required String password,
    String? email,
    DateTime? dateOfBirth,
  }) async {
    final response = await _api.post(
      Endpoints.register,
      body: {
        'full_name': fullName,
        'phone': phone,
        'password': password,
        if (email != null) 'email': email,
        if (dateOfBirth != null) 'date_of_birth': dateOfBirth.toIso8601String().split('T')[0],
      },
      auth: false,
    );
    await _saveTokens(response);
    return AuthResult.fromJson(response);
  }

  Future<void> verifyPhone(String phone, String code) async {
    await _api.post(
      Endpoints.verifyPhone,
      body: {'phone': phone, 'code': code},
      auth: false,
    );
  }

  Future<void> forgotPassword(String phone) async {
    await _api.post(
      Endpoints.forgotPassword,
      body: {'phone': phone},
      auth: false,
    );
  }

  Future<void> resetPassword(String phone, String code, String newPassword) async {
    await _api.post(
      Endpoints.resetPassword,
      body: {
        'phone': phone,
        'code': code,
        'new_password': newPassword,
      },
      auth: false,
    );
  }

  Future<void> changePassword(String currentPassword, String newPassword) async {
    await _api.post(
      Endpoints.changePassword,
      body: {
        'current_password': currentPassword,
        'new_password': newPassword,
      },
    );
  }

  Future<Customer?> getProfile() async {
    try {
      final response = await _api.get(Endpoints.customerProfile);
      return Customer.fromJson(response);
    } catch (_) {
      return null;
    }
  }

  Future<void> logout() async {
    await _tokenStorage.clearTokens();
  }

  Future<bool> isLoggedIn() => _tokenStorage.isLoggedIn();

  Future<bool> isBiometricEnabled() => _tokenStorage.isBiometricEnabled();

  Future<void> setBiometricEnabled(bool enabled) =>
      _tokenStorage.setBiometricEnabled(enabled);

  Future<String?> getUserRole() => _tokenStorage.getUserRole();

  Future<AuthResult> refreshToken() async {
    final refreshToken = await _tokenStorage.getRefreshToken();
    if (refreshToken == null) throw Exception('No refresh token');
    final response = await _api.post(
      Endpoints.refreshToken,
      body: {'refresh_token': refreshToken},
      auth: false,
    );
    await _saveTokens(response);
    return AuthResult.fromJson(response);
  }

  Future<void> _saveTokens(Map<String, dynamic> response) async {
    await _tokenStorage.saveTokens(
      accessToken: response['access_token'],
      refreshToken: response['refresh_token'],
    );
    if (response['user'] != null) {
      await _tokenStorage.saveUserDetails(
        role: response['user']['role'] ?? 'customer',
        userId: response['user']['id'],
      );
    }
  }
}

class AuthResult {
  final String accessToken;
  final String? refreshToken;
  final Customer? user;

  AuthResult({
    required this.accessToken,
    this.refreshToken,
    this.user,
  });

  factory AuthResult.fromJson(Map<String, dynamic> json) {
    return AuthResult(
      accessToken: json['access_token'] ?? '',
      refreshToken: json['refresh_token'],
      user: json['user'] != null ? Customer.fromJson(json['user']) : null,
    );
  }
}
