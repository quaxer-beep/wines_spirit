import 'dart:async';
import 'package:flutter/material.dart';
import 'package:shared_core/shared_core.dart';

class RiderLocationProvider extends ChangeNotifier {
  final ApiClient _apiClient;
  RiderLocation? _currentLocation;
  bool _isTracking = false;
  Timer? _locationTimer;
  int _riderId = 0;

  RiderLocationProvider({required ApiClient apiClient}) : _apiClient = apiClient;

  RiderLocation? get currentLocation => _currentLocation;
  bool get isTracking => _isTracking;

  void setRiderId(int id) {
    _riderId = id;
  }

  void startTracking() {
    if (_isTracking) return;
    _isTracking = true;
    notifyListeners();

    _locationTimer = Timer.periodic(
      const Duration(seconds: 30),
      (_) => _simulateLocationUpdate(),
    );
  }

  void stopTracking() {
    _isTracking = false;
    _locationTimer?.cancel();
    _locationTimer = null;
    notifyListeners();
  }

  Future<void> updateLocation(double latitude, double longitude) async {
    _currentLocation = RiderLocation(
      riderId: _riderId,
      latitude: latitude,
      longitude: longitude,
      lastUpdated: DateTime.now().toIso8601String(),
    );
    notifyListeners();

    try {
      await _apiClient.post(
        Endpoints.mobileLocationUpdate,
        body: {
          'latitude': latitude,
          'longitude': longitude,
          'timestamp': DateTime.now().toIso8601String(),
        },
      );
    } catch (_) {}
  }

  Future<List<RiderLocation>> getLocationHistory(int deliveryId) async {
    try {
      final response = await _apiClient.get(
        '${Endpoints.mobileLocationHistory}?delivery_id=$deliveryId',
      );
      final list = (response['locations'] as List?) ?? [];
      return list.map((l) => RiderLocation.fromJson(l)).toList();
    } catch (_) {
      return [];
    }
  }

  Future<void> _simulateLocationUpdate() async {
    final lat = _currentLocation?.latitude ?? -1.2921;
    final lng = _currentLocation?.longitude ?? 36.8219;
    final newLat = lat + (DateTime.now().millisecondsSinceEpoch % 100) * 0.00001;
    final newLng = lng + (DateTime.now().millisecondsSinceEpoch % 100) * 0.00001;
    await updateLocation(newLat, newLng);
  }

  @override
  void dispose() {
    stopTracking();
    super.dispose();
  }
}
