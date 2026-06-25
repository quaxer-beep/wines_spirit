class Address {
  final int id;
  final int customerId;
  final String? label;
  final String address;
  final String? buildingName;
  final String? landmark;
  final double? latitude;
  final double? longitude;
  final bool isDefault;

  Address({
    required this.id,
    required this.customerId,
    this.label,
    required this.address,
    this.buildingName,
    this.landmark,
    this.latitude,
    this.longitude,
    this.isDefault = false,
  });

  factory Address.fromJson(Map<String, dynamic> json) {
    return Address(
      id: json['id'],
      customerId: json['customer_id'],
      label: json['label'],
      address: json['address'] ?? '',
      buildingName: json['building_name'],
      landmark: json['landmark'],
      latitude: (json['latitude'] as num?)?.toDouble(),
      longitude: (json['longitude'] as num?)?.toDouble(),
      isDefault: json['is_default'] ?? false,
    );
  }

  Map<String, dynamic> toJson() => {
        'label': label,
        'address': address,
        'building_name': buildingName,
        'landmark': landmark,
        'latitude': latitude,
        'longitude': longitude,
        'is_default': isDefault,
      };
}
