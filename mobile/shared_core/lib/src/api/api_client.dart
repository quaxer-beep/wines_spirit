import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;

import 'endpoints.dart';
import 'api_exceptions.dart';
import '../auth/token_storage.dart';

class ApiClient {
  final TokenStorage _tokenStorage;
  final http.Client _httpClient;
  String? _baseUrl;

  ApiClient({
    required TokenStorage tokenStorage,
    http.Client? httpClient,
    String? baseUrl,
  })  : _tokenStorage = tokenStorage,
        _httpClient = httpClient ?? http.Client(),
        _baseUrl = baseUrl ?? Endpoints.baseUrl;

  set baseUrl(String url) => _baseUrl = url;

  Future<Map<String, String>> _getHeaders({bool auth = true}) async {
    final headers = <String, String>{
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };
    if (auth) {
      final token = await _tokenStorage.getAccessToken();
      if (token != null) {
        headers['Authorization'] = 'Bearer $token';
      }
    }
    return headers;
  }

  Future<dynamic> _handleResponse(http.Response response) async {
    final body = response.body.isNotEmpty
        ? jsonDecode(response.body)
        : <String, dynamic>{};

    if (response.statusCode >= 200 && response.statusCode < 300) {
      return body;
    }

    if (response.statusCode == 401) {
      final refreshed = await _tryRefreshToken();
      if (refreshed) {
        throw ApiException(
          message: 'Token expired, retry request',
          statusCode: 401,
        );
      }
      await _tokenStorage.clearTokens();
      throw ApiException(
        message: body['detail'] ?? 'Unauthorized',
        statusCode: 401,
      );
    }

    throw ApiException(
      message: body['detail'] ?? 'Request failed',
      statusCode: response.statusCode,
      errors: body['errors'],
    );
  }

  Future<bool> _tryRefreshToken() async {
    final refreshToken = await _tokenStorage.getRefreshToken();
    if (refreshToken == null) return false;

    try {
      final response = await _httpClient.post(
        Uri.parse('$_baseUrl${Endpoints.refreshToken}'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'refresh_token': refreshToken}),
      );
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        await _tokenStorage.saveTokens(
          accessToken: data['access_token'],
          refreshToken: data['refresh_token'] ?? refreshToken,
        );
        return true;
      }
    } catch (_) {}
    return false;
  }

  Duration get _timeout => const Duration(seconds: 30);

  Future<dynamic> get(String path, {Map<String, String>? queryParams}) async {
    try {
      final uri = Uri.parse('$_baseUrl$path').replace(queryParameters: queryParams);
      final response = await _httpClient
          .get(uri, headers: await _getHeaders())
          .timeout(_timeout);
      return _handleResponse(response);
    } on SocketException {
      throw NetworkException();
    } on http.ClientException {
      throw NetworkException();
    }
  }

  Future<dynamic> post(String path, {Map<String, dynamic>? body, bool auth = true}) async {
    try {
      final response = await _httpClient
          .post(
            Uri.parse('$_baseUrl$path'),
            headers: await _getHeaders(auth: auth),
            body: body != null ? jsonEncode(body) : null,
          )
          .timeout(_timeout);
      return _handleResponse(response);
    } on SocketException {
      throw NetworkException();
    } on http.ClientException {
      throw NetworkException();
    }
  }

  Future<dynamic> put(String path, {Map<String, dynamic>? body}) async {
    try {
      final response = await _httpClient
          .put(
            Uri.parse('$_baseUrl$path'),
            headers: await _getHeaders(),
            body: body != null ? jsonEncode(body) : null,
          )
          .timeout(_timeout);
      return _handleResponse(response);
    } on SocketException {
      throw NetworkException();
    } on http.ClientException {
      throw NetworkException();
    }
  }

  Future<dynamic> delete(String path) async {
    try {
      final response = await _httpClient
          .delete(Uri.parse('$_baseUrl$path'), headers: await _getHeaders())
          .timeout(_timeout);
      return _handleResponse(response);
    } on SocketException {
      throw NetworkException();
    } on http.ClientException {
      throw NetworkException();
    }
  }

  void dispose() {
    _httpClient.close();
  }
}
