import 'package:flutter/material.dart';
import 'package:shared_core/shared_core.dart';

class RiderIncidentProvider extends ChangeNotifier {
  final ApiClient _apiClient;
  List<DeliveryIncident> _incidents = [];
  bool _isLoading = false;
  String? _error;

  RiderIncidentProvider({required ApiClient apiClient}) : _apiClient = apiClient;

  List<DeliveryIncident> get incidents => _incidents;
  bool get isLoading => _isLoading;
  String? get error => _error;

  Future<void> fetchIncidents() async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final response = await _apiClient.get(Endpoints.mobileIncidents);
      final list = (response['incidents'] as List?) ?? [];
      _incidents = list.map((i) => DeliveryIncident.fromJson(i)).toList();
      _isLoading = false;
      notifyListeners();
    } on ApiException catch (e) {
      _error = e.message;
      _isLoading = false;
      notifyListeners();
    } catch (e) {
      _error = 'Failed to load incidents.';
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<bool> reportIncident({
    required int deliveryId,
    required String type,
    String? description,
    String? photo,
    double? latitude,
    double? longitude,
  }) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final body = <String, dynamic>{
        'delivery_id': deliveryId,
        'incident_type': type,
        if (description != null) 'description': description,
        if (photo != null) 'photo': photo,
        if (latitude != null) 'latitude': latitude,
        if (longitude != null) 'longitude': longitude,
      };
      await _apiClient.post(Endpoints.mobileIncidents, body: body);
      await fetchIncidents();
      _isLoading = false;
      notifyListeners();
      return true;
    } on ApiException catch (e) {
      _error = e.message;
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  Future<bool> resolveIncident(int id, String resolutionNote) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      await _apiClient.post(
        Endpoints.mobileIncidentResolve(id),
        body: {'resolution_notes': resolutionNote},
      );
      await fetchIncidents();
      _isLoading = false;
      notifyListeners();
      return true;
    } on ApiException catch (e) {
      _error = e.message;
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  void clearError() {
    _error = null;
    notifyListeners();
  }
}
