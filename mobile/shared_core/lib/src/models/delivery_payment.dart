class DeliveryPayment {
  final int id;
  final int orderId;
  final int? riderId;
  final String customerPhone;
  final String? mpesaReceipt;
  final double amount;
  final String status;
  final DateTime? paymentTimestamp;
  final DateTime createdAt;

  DeliveryPayment({
    required this.id,
    required this.orderId,
    this.riderId,
    required this.customerPhone,
    this.mpesaReceipt,
    required this.amount,
    required this.status,
    this.paymentTimestamp,
    required this.createdAt,
  });

  factory DeliveryPayment.fromJson(Map<String, dynamic> json) => DeliveryPayment(
    id: json['id'] as int,
    orderId: json['order_id'] as int,
    riderId: json['rider_id'] as int?,
    customerPhone: json['customer_phone'] as String,
    mpesaReceipt: json['mpesa_receipt'] as String?,
    amount: (json['amount'] as num).toDouble(),
    status: json['status'] as String,
    paymentTimestamp: json['payment_timestamp'] != null ? DateTime.parse(json['payment_timestamp'] as String) : null,
    createdAt: DateTime.parse(json['created_at'] as String),
  );

  Map<String, dynamic> toJson() => {
    'id': id,
    'order_id': orderId,
    'rider_id': riderId,
    'customer_phone': customerPhone,
    'mpesa_receipt': mpesaReceipt,
    'amount': amount,
    'status': status,
    'payment_timestamp': paymentTimestamp?.toIso8601String(),
    'created_at': createdAt.toIso8601String(),
  };

  bool get isCompleted => status == 'completed';
  bool get isPending => status == 'pending';
  bool get isFailed => status == 'failed';
}
