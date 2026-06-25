class DeliveryAgeVerification {
  final int id;
  final int orderId;
  final int? riderId;
  final String documentType;
  final String documentNumber;
  final DateTime verificationTimestamp;

  DeliveryAgeVerification({
    required this.id,
    required this.orderId,
    this.riderId,
    required this.documentType,
    required this.documentNumber,
    required this.verificationTimestamp,
  });

  factory DeliveryAgeVerification.fromJson(Map<String, dynamic> json) => DeliveryAgeVerification(
    id: json['id'] as int,
    orderId: json['order_id'] as int,
    riderId: json['rider_id'] as int?,
    documentType: json['document_type'] as String,
    documentNumber: json['document_number'] as String,
    verificationTimestamp: DateTime.parse(json['verification_timestamp'] as String),
  );

  Map<String, dynamic> toJson() => {
    'id': id,
    'order_id': orderId,
    'rider_id': riderId,
    'document_type': documentType,
    'document_number': documentNumber,
    'verification_timestamp': verificationTimestamp.toIso8601String(),
  };
}
