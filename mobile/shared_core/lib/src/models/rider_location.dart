class RiderLocation {
  final int riderId;
  final double latitude;
  final double longitude;
  final double? speed;
  final double? bearing;
  final double? batteryLevel;
  final String? lastUpdated;
  final int? deliveryId;
  final String? riderName;
  final String? riderPhone;
  final String? vehicleType;
  final double? distanceKm;

  RiderLocation({
    required this.riderId,
    required this.latitude,
    required this.longitude,
    this.speed,
    this.bearing,
    this.batteryLevel,
    this.lastUpdated,
    this.deliveryId,
    this.riderName,
    this.riderPhone,
    this.vehicleType,
    this.distanceKm,
  });

  factory RiderLocation.fromJson(Map<String, dynamic> json) {
    return RiderLocation(
      riderId: json['rider_id'],
      latitude: (json['latitude'] as num).toDouble(),
      longitude: (json['longitude'] as num).toDouble(),
      speed: (json['speed'] as num?)?.toDouble(),
      bearing: (json['bearing'] as num?)?.toDouble(),
      batteryLevel: (json['battery_level'] as num?)?.toDouble(),
      lastUpdated: json['last_updated'],
      deliveryId: json['delivery_id'],
      riderName: json['rider_name'],
      riderPhone: json['rider_phone'],
      vehicleType: json['vehicle_type'],
      distanceKm: (json['distance_km'] as num?)?.toDouble(),
    );
  }
}
