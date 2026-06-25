class Rider {
  final int id;
  final String name;
  final String phone;
  final String? email;
  final String vehicleType;
  final String plateNumber;
  final String status;
  final int? branchId;
  final bool isActive;
  final double? lastLatitude;
  final double? lastLongitude;

  Rider({
    required this.id,
    required this.name,
    required this.phone,
    this.email,
    required this.vehicleType,
    required this.plateNumber,
    this.status = 'available',
    this.branchId,
    this.isActive = true,
    this.lastLatitude,
    this.lastLongitude,
  });

  factory Rider.fromJson(Map<String, dynamic> json) {
    return Rider(
      id: json['id'],
      name: json['name'] ?? '',
      phone: json['phone'] ?? '',
      email: json['email'],
      vehicleType: json['vehicle_type'] ?? '',
      plateNumber: json['plate_number'] ?? '',
      status: json['status'] ?? 'available',
      branchId: json['branch_id'],
      isActive: json['is_active'] ?? true,
      lastLatitude: (json['last_latitude'] as num?)?.toDouble(),
      lastLongitude: (json['last_longitude'] as num?)?.toDouble(),
    );
  }

  bool get isAvailable => status == 'available';
  bool get isBusy => status == 'busy';
  bool get isOffline => status == 'offline';
}
