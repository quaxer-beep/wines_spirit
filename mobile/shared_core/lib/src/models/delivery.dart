class RiderDelivery {
  final int id;
  final int orderId;
  final int? riderId;
  final String address;
  final double? latitude;
  final double? longitude;
  final double? distanceKm;
  final double deliveryFee;
  final String status;
  final String? customerName;
  final String? customerPhone;
  final String? startedAt;
  final String? pickedUpAt;
  final String? deliveredAt;
  final String? notes;
  final String createdAt;

  RiderDelivery({
    required this.id,
    required this.orderId,
    this.riderId,
    required this.address,
    this.latitude,
    this.longitude,
    this.distanceKm,
    this.deliveryFee = 0,
    this.status = 'pending',
    this.customerName,
    this.customerPhone,
    this.startedAt,
    this.pickedUpAt,
    this.deliveredAt,
    this.notes,
    required this.createdAt,
  });

  factory RiderDelivery.fromJson(Map<String, dynamic> json) {
    return RiderDelivery(
      id: json['id'],
      orderId: json['order_id'],
      riderId: json['rider_id'],
      address: json['address'] ?? '',
      latitude: (json['latitude'] as num?)?.toDouble(),
      longitude: (json['longitude'] as num?)?.toDouble(),
      distanceKm: (json['distance_km'] as num?)?.toDouble(),
      deliveryFee: (json['delivery_fee'] as num?)?.toDouble() ?? 0,
      status: json['status'] ?? 'pending',
      customerName: json['customer_name'] ?? json['customer']['full_name'],
      customerPhone: json['customer_phone'] ?? json['customer']['phone'],
      startedAt: json['started_at'],
      pickedUpAt: json['picked_up_at'],
      deliveredAt: json['delivered_at'],
      notes: json['notes'],
      createdAt: json['created_at'] ?? '',
    );
  }

  bool get isAssigned => status == 'assigned';
  bool get isAccepted => status == 'accepted';
  bool get isPickedUp => status == 'picked_up';
  bool get isEnRoute => status == 'en_route';
  bool get isDelivered => status == 'delivered';
  bool get isFailed => status == 'failed';

  String get statusLabel {
    switch (status) {
      case 'assigned': return 'Assigned';
      case 'accepted': return 'Accepted';
      case 'picked_up': return 'Picked Up';
      case 'en_route': return 'En Route';
      case 'delivered': return 'Delivered';
      case 'failed': return 'Failed';
      default: return status;
    }
  }
}

class DeliveryVerification {
  final int id;
  final int deliveryId;
  final int orderId;
  final String recipientName;
  final bool idChecked;
  final bool ageConfirmed;
  final bool verificationPassed;
  final String? verificationTime;
  final String? riderNotes;

  DeliveryVerification({
    required this.id,
    required this.deliveryId,
    required this.orderId,
    required this.recipientName,
    this.idChecked = false,
    this.ageConfirmed = false,
    this.verificationPassed = false,
    this.verificationTime,
    this.riderNotes,
  });

  factory DeliveryVerification.fromJson(Map<String, dynamic> json) {
    return DeliveryVerification(
      id: json['id'],
      deliveryId: json['delivery_id'],
      orderId: json['order_id'],
      recipientName: json['recipient_name'] ?? '',
      idChecked: json['id_checked'] ?? false,
      ageConfirmed: json['age_confirmed'] ?? false,
      verificationPassed: json['verification_passed'] ?? false,
      verificationTime: json['verification_time'],
      riderNotes: json['rider_notes'],
    );
  }
}
