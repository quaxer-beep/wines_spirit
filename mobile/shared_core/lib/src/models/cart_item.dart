import 'product.dart';

class CartItem {
  final int id;
  final int productId;
  final String productName;
  final double unitPrice;
  final int quantity;
  final String? productImage;
  final bool requiresAgeVerification;

  CartItem({
    required this.id,
    required this.productId,
    required this.productName,
    required this.unitPrice,
    required this.quantity,
    this.productImage,
    this.requiresAgeVerification = false,
  });

  double get subtotal => unitPrice * quantity;

  String get formattedSubtotal => 'KSh ${subtotal.toStringAsFixed(0)}';
  String get formattedUnitPrice => 'KSh ${unitPrice.toStringAsFixed(0)}';

  factory CartItem.fromJson(Map<String, dynamic> json) {
    return CartItem(
      id: json['id'],
      productId: json['product_id'],
      productName: json['product_name'] ?? '',
      unitPrice: (json['unit_price'] as num?)?.toDouble() ?? 0,
      quantity: json['quantity'] ?? 1,
      productImage: json['product_image'],
      requiresAgeVerification: json['requires_age_verification'] ?? false,
    );
  }

  factory CartItem.fromProduct(Product product, {int quantity = 1}) {
    return CartItem(
      id: 0,
      productId: product.id,
      productName: product.name,
      unitPrice: product.sellingPrice,
      quantity: quantity,
      productImage: product.imageUrl,
      requiresAgeVerification: product.requiresAgeVerification,
    );
  }
}

class Cart {
  final List<CartItem> items;
  final double subtotal;
  final double deliveryFee;
  final double discount;
  final double total;

  Cart({
    this.items = const [],
    this.subtotal = 0,
    this.deliveryFee = 0,
    this.discount = 0,
    this.total = 0,
  });

  factory Cart.fromJson(Map<String, dynamic> json) {
    return Cart(
      items: (json['items'] as List?)?.map((i) => CartItem.fromJson(i)).toList() ?? [],
      subtotal: (json['subtotal'] as num?)?.toDouble() ?? 0,
      deliveryFee: (json['delivery_fee'] as num?)?.toDouble() ?? 0,
      discount: (json['discount'] as num?)?.toDouble() ?? 0,
      total: (json['total'] as num?)?.toDouble() ?? 0,
    );
  }

  int get itemCount => items.fold(0, (sum, item) => sum + item.quantity);
}
