class Promotion {
  final int id;
  final String name;
  final String? description;
  final String promotionType;
  final String? discountType;
  final double? discountValue;
  final int? productId;
  final String? category;
  final double? minOrderAmount;
  final double? maxDiscount;
  final bool isActive;
  final String startDate;
  final String endDate;

  Promotion({
    required this.id,
    required this.name,
    this.description,
    required this.promotionType,
    this.discountType,
    this.discountValue,
    this.productId,
    this.category,
    this.minOrderAmount,
    this.maxDiscount,
    this.isActive = true,
    required this.startDate,
    required this.endDate,
  });

  factory Promotion.fromJson(Map<String, dynamic> json) {
    return Promotion(
      id: json['id'],
      name: json['name'] ?? '',
      description: json['description'],
      promotionType: json['promotion_type'] ?? '',
      discountType: json['discount_type'],
      discountValue: (json['discount_value'] as num?)?.toDouble(),
      productId: json['product_id'],
      category: json['category'],
      minOrderAmount: (json['min_order_amount'] as num?)?.toDouble(),
      maxDiscount: (json['max_discount'] as num?)?.toDouble(),
      isActive: json['is_active'] ?? true,
      startDate: json['start_date'] ?? '',
      endDate: json['end_date'] ?? '',
    );
  }

  String get discountLabel {
    if (discountType == 'percentage' && discountValue != null) {
      return '${discountValue!.toInt()}% OFF';
    }
    if (discountValue != null) {
      return 'KSh ${discountValue!.toInt()} OFF';
    }
    return promotionType;
  }
}
