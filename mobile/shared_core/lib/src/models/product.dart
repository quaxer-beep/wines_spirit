class Product {
  final int id;
  final String name;
  final String? brand;
  final String category;
  final String? description;
  final double sellingPrice;
  final double costPrice;
  final String unit;
  final int reorderLevel;
  final bool isActive;
  final bool isAlcoholic;
  final bool requiresAgeVerification;
  final int stockQuantity;
  final int branchId;
  final List<String> images;
  final double? averageRating;

  Product({
    required this.id,
    required this.name,
    this.brand,
    required this.category,
    this.description,
    required this.sellingPrice,
    this.costPrice = 0,
    this.unit = 'pcs',
    this.reorderLevel = 0,
    this.isActive = true,
    this.isAlcoholic = true,
    this.requiresAgeVerification = true,
    this.stockQuantity = 0,
    this.branchId = 0,
    this.images = const [],
    this.averageRating,
  });

  factory Product.fromJson(Map<String, dynamic> json) {
    return Product(
      id: json['id'],
      name: json['name'] ?? '',
      brand: json['brand'],
      category: json['category'] ?? '',
      description: json['description'],
      sellingPrice: (json['selling_price'] as num?)?.toDouble() ?? 0,
      costPrice: (json['cost_price'] as num?)?.toDouble() ?? 0,
      unit: json['unit'] ?? 'pcs',
      reorderLevel: json['reorder_level'] ?? 0,
      isActive: json['is_active'] ?? true,
      isAlcoholic: json['is_alcoholic'] ?? true,
      requiresAgeVerification: json['requires_age_verification'] ?? true,
      stockQuantity: json['stock_quantity'] ?? 0,
      branchId: json['branch_id'] ?? 0,
      images: (json['images'] as List?)?.map((i) => i is String ? i : i['url'] ?? '').toList() ?? [],
      averageRating: (json['average_rating'] as num?)?.toDouble(),
    );
  }

  String get formattedPrice => 'KSh ${sellingPrice.toStringAsFixed(0)}';

  String get imageUrl => images.isNotEmpty ? images.first : '';

  bool get inStock => stockQuantity > 0;
  bool get lowStock => stockQuantity > 0 && stockQuantity <= reorderLevel;

  String get stockLabel {
    if (stockQuantity <= 0) return 'Out of Stock';
    if (lowStock) return 'Low Stock ($stockQuantity)';
    return 'In Stock ($stockQuantity)';
  }
}

class ProductCategory {
  final String name;
  final String? icon;
  final int productCount;

  ProductCategory({
    required this.name,
    this.icon,
    this.productCount = 0,
  });

  factory ProductCategory.fromJson(Map<String, dynamic> json) {
    return ProductCategory(
      name: json['name'] ?? '',
      icon: json['icon'],
      productCount: json['product_count'] ?? 0,
    );
  }
}
