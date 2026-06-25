import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shared_core/shared_core.dart';
import '../../providers/product_provider.dart';
import '../../providers/cart_provider.dart';

class ProductDetailScreen extends StatelessWidget {
  final int productId;
  const ProductDetailScreen({super.key, required this.productId});

  @override
  Widget build(BuildContext context) {
    final product = context.watch<ProductProvider>().getProductById(productId);
    if (product == null) {
      return Scaffold(
        appBar: AppBar(),
        body: const Center(child: Text('Product not found')),
      );
    }

    final cart = context.watch<CartProvider>();

    return Scaffold(
      body: CustomScrollView(
        slivers: [
          SliverAppBar(
            expandedHeight: 300,
            pinned: true,
            flexibleSpace: FlexibleSpaceBar(
              background: Container(
                color: AppColors.surfaceVariant,
                child: product.imageUrl.isNotEmpty
                    ? Image.network(
                        product.imageUrl,
                        fit: BoxFit.cover,
                        errorBuilder: (_, __, ___) => const Icon(
                          Icons.wine_bottle,
                          size: 64,
                          color: AppColors.textHint,
                        ),
                      )
                    : const Icon(
                        Icons.wine_bottle,
                        size: 64,
                        color: AppColors.textHint,
                      ),
              ),
            ),
          ),
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (product.brand != null)
                    Text(product.brand!,
                        style: AppTextStyles.caption),
                  Text(product.name, style: AppTextStyles.headlineMedium),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      Text(product.formattedPrice,
                          style: AppTextStyles.displaySmall?.copyWith(
                              color: AppColors.primary)),
                      const Spacer(),
                      AgeVerificationBadge(
                        isVerified: product.requiresAgeVerification == false,
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  Text('Category: ${product.category}',
                      style: AppTextStyles.bodyMedium),
                  const SizedBox(height: 8),
                  Text('Unit: ${product.unit}',
                      style: AppTextStyles.bodyMedium),
                  const SizedBox(height: 8),
                  Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                    decoration: BoxDecoration(
                      color: product.inStock
                          ? AppColors.success.withAlpha(25)
                          : AppColors.error.withAlpha(25),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Text(
                      product.stockLabel,
                      style: TextStyle(
                        color: product.inStock
                            ? AppColors.success
                            : AppColors.error,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ),
                  if (product.description != null &&
                      product.description!.isNotEmpty) ...[
                    const SizedBox(height: 16),
                    Text('Description',
                        style: AppTextStyles.titleLarge),
                    const SizedBox(height: 8),
                    Text(product.description!,
                        style: AppTextStyles.bodyMedium),
                  ],
                  const SizedBox(height: 16),
                  Text('Requires Age Verification',
                      style: AppTextStyles.titleLarge),
                  const SizedBox(height: 4),
                  Text(
                    product.requiresAgeVerification
                        ? 'You must verify your age to purchase this product'
                        : 'No age verification required',
                    style: AppTextStyles.bodySmall,
                  ),
                  const SizedBox(height: 80),
                ],
              ),
            ),
          ),
        ],
      ),
      bottomNavigationBar: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              Expanded(
                child: OutlinedButton(
                  onPressed: () => Navigator.pop(context),
                  child: const Text('Back'),
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                flex: 2,
                child: ElevatedButton.icon(
                  onPressed: product.inStock
                      ? () => cart.addItem(product)
                      : null,
                  icon: const Icon(Icons.add_shopping_cart),
                  label: Text(product.inStock ? 'Add to Cart' : 'Out of Stock'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
