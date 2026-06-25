class DeliveryIncident {
  final int id;
  final int deliveryId;
  final int? riderId;
  final String incidentType;
  final String? description;
  final bool customerNotified;
  final bool branchNotified;
  final String resolutionStatus;
  final String? resolvedAt;
  final String? resolutionNotes;
  final String createdAt;

  DeliveryIncident({
    required this.id,
    required this.deliveryId,
    this.riderId,
    required this.incidentType,
    this.description,
    this.customerNotified = false,
    this.branchNotified = false,
    this.resolutionStatus = 'open',
    this.resolvedAt,
    this.resolutionNotes,
    required this.createdAt,
  });

  factory DeliveryIncident.fromJson(Map<String, dynamic> json) {
    return DeliveryIncident(
      id: json['id'],
      deliveryId: json['delivery_id'],
      riderId: json['rider_id'],
      incidentType: json['incident_type'] ?? '',
      description: json['description'],
      customerNotified: json['customer_notified'] ?? false,
      branchNotified: json['branch_notified'] ?? false,
      resolutionStatus: json['resolution_status'] ?? 'open',
      resolvedAt: json['resolved_at'],
      resolutionNotes: json['resolution_notes'],
      createdAt: json['created_at'] ?? '',
    );
  }

  String get incidentTypeLabel {
    switch (incidentType) {
      case 'customer_not_available': return 'Customer Not Available';
      case 'invalid_address': return 'Invalid Address';
      case 'underage_recipient': return 'Underage Recipient';
      case 'refused_delivery': return 'Refused Delivery';
      case 'product_damage': return 'Product Damage';
      case 'other': return 'Other';
      default: return incidentType;
    }
  }

  bool get isOpen => resolutionStatus == 'open';
  bool get isResolved => resolutionStatus == 'resolved';
  bool get isDismissed => resolutionStatus == 'dismissed';
}
