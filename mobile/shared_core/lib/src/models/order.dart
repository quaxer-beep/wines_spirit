class OrderItem {
  final int id;
  final int productId;
  final String productName;
  final int quantity;
  final double unitPrice;
  final double subtotal;

  OrderItem({
    required this.id,
    required this.productId,
    required this.productName,
    required this.quantity,
    required this.unitPrice,
    required this.subtotal,
  });

  factory OrderItem.fromJson(Map<String, dynamic> json) {
    return OrderItem(
      id: json['id'],
      productId: json['product_id'],
      productName: json['product_name'] ?? '',
      quantity: json['quantity'] ?? 0,
      unitPrice: (json['unit_price'] as num?)?.toDouble() ?? 0,
      subtotal: (json['subtotal'] as num?)?.toDouble() ?? 0,
    );
  }
}

class Order {
  final int id;
  final String orderNumber;
  final int customerId;
  final int? branchId;
  final double subtotal;
  final double deliveryFee;
  final double discount;
  final double tax;
  final double grandTotal;
  final String status;
  final String paymentStatus;
  final String deliveryStatus;
  final String? notes;
  final String createdAt;
  final String? updatedAt;
  final List<OrderItem> items;
  final List<PaymentInfo> payments;

  Order({
    required this.id,
    required this.orderNumber,
    required this.customerId,
    this.branchId,
    this.subtotal = 0,
    this.deliveryFee = 0,
    this.discount = 0,
    this.tax = 0,
    this.grandTotal = 0,
    this.status = 'pending',
    this.paymentStatus = 'pending',
    this.deliveryStatus = 'pending',
    this.notes,
    required this.createdAt,
    this.updatedAt,
    this.items = const [],
    this.payments = const [],
  });

  factory Order.fromJson(Map<String, dynamic> json) {
    return Order(
      id: json['id'],
      orderNumber: json['order_number'] ?? '',
      customerId: json['customer_id'],
      branchId: json['branch_id'],
      subtotal: (json['subtotal'] as num?)?.toDouble() ?? 0,
      deliveryFee: (json['delivery_fee'] as num?)?.toDouble() ?? 0,
      discount: (json['discount'] as num?)?.toDouble() ?? 0,
      tax: (json['tax'] as num?)?.toDouble() ?? 0,
      grandTotal: (json['grand_total'] as num?)?.toDouble() ?? 0,
      status: json['status'] ?? 'pending',
      paymentStatus: json['payment_status'] ?? 'pending',
      deliveryStatus: json['delivery_status'] ?? 'pending',
      notes: json['notes'],
      createdAt: json['created_at'] ?? '',
      updatedAt: json['updated_at'],
      items: (json['items'] as List?)?.map((i) => OrderItem.fromJson(i)).toList() ?? [],
      payments: (json['payments'] as List?)?.map((p) => PaymentInfo.fromJson(p)).toList() ?? [],
    );
  }

  String get formattedTotal => 'KSh ${grandTotal.toStringAsFixed(0)}';

  bool get isPending => status == 'pending';
  bool get isConfirmed => status == 'confirmed';
  bool get isPreparing => status == 'preparing';
  bool get isOutForDelivery => status == 'out_for_delivery';
  bool get isDelivered => status == 'delivered';
  bool get isCancelled => status == 'cancelled';

  bool get isPaid => paymentStatus == 'paid';
  bool get isPaymentPending => paymentStatus == 'pending';

  String get statusLabel {
    switch (status) {
      case 'pending': return 'Pending';
      case 'confirmed': return 'Confirmed';
      case 'preparing': return 'Preparing';
      case 'out_for_delivery': return 'Out for Delivery';
      case 'delivered': return 'Delivered';
      case 'cancelled': return 'Cancelled';
      default: return status;
    }
  }

  int get statusIndex {
    const statuses = ['pending', 'confirmed', 'preparing', 'out_for_delivery', 'delivered'];
    return statuses.indexOf(status);
  }
}

class PaymentInfo {
  final int id;
  final String method;
  final double amount;
  final String? receiptNumber;
  final String? phoneNumber;
  final String status;

  PaymentInfo({
    required this.id,
    this.method = 'MPESA',
    required this.amount,
    this.receiptNumber,
    this.phoneNumber,
    this.status = 'pending',
  });

  factory PaymentInfo.fromJson(Map<String, dynamic> json) {
    return PaymentInfo(
      id: json['id'],
      method: json['method'] ?? 'MPESA',
      amount: (json['amount'] as num?)?.toDouble() ?? 0,
      receiptNumber: json['receipt_number'],
      phoneNumber: json['phone_number'],
      status: json['status'] ?? 'pending',
    );
  }
}

class Delivery {
  final int id;
  final int orderId;
  final int? riderId;
  final String address;
  final double? latitude;
  final double? longitude;
  final double? distanceKm;
  final int? estimatedDurationMinutes;
  final double deliveryFee;
  final String status;
  final String? riderName;
  final String? riderPhone;
  final String? startedAt;
  final String? pickedUpAt;
  final String? deliveredAt;

  Delivery({
    required this.id,
    required this.orderId,
    this.riderId,
    required this.address,
    this.latitude,
    this.longitude,
    this.distanceKm,
    this.estimatedDurationMinutes,
    this.deliveryFee = 0,
    this.status = 'pending',
    this.riderName,
    this.riderPhone,
    this.startedAt,
    this.pickedUpAt,
    this.deliveredAt,
  });

  factory Delivery.fromJson(Map<String, dynamic> json) {
    return Delivery(
      id: json['id'],
      orderId: json['order_id'],
      riderId: json['rider_id'],
      address: json['address'] ?? '',
      latitude: (json['latitude'] as num?)?.toDouble(),
      longitude: (json['longitude'] as num?)?.toDouble(),
      distanceKm: (json['distance_km'] as num?)?.toDouble(),
      estimatedDurationMinutes: json['estimated_duration_minutes'],
      deliveryFee: (json['delivery_fee'] as num?)?.toDouble() ?? 0,
      status: json['status'] ?? 'pending',
      riderName: json['rider_name'],
      riderPhone: json['rider_phone'],
      startedAt: json['started_at'],
      pickedUpAt: json['picked_up_at'],
      deliveredAt: json['delivered_at'],
    );
  }
}
