import 'package:flutter/material.dart';
import 'package:shared_core/shared_core.dart';

class ProductProvider extends ChangeNotifier {
  final ApiClient _apiClient;
  List<Product> _products = [];
  List<ProductCategory> _categories = [];
  List<Product> _featuredProducts = [];
  List<Promotion> _promotions = [];
  bool _isLoading = false;
  String? _error;
  String _selectedCategory = 'All';
  String _searchQuery = '';

  ProductProvider({required ApiClient apiClient}) : _apiClient = apiClient;

  List<Product> get products => _filteredProducts;
  List<ProductCategory> get categories => _categories;
  List<Product> get featuredProducts => _featuredProducts;
  List<Promotion> get promotions => _promotions;
  bool get isLoading => _isLoading;
  String? get error => _error;
  String get selectedCategory => _selectedCategory;

  List<Product> get _filteredProducts {
    var filtered = _products;
    if (_selectedCategory != 'All') {
      filtered = filtered.where((p) => p.category == _selectedCategory).toList();
    }
    if (_searchQuery.isNotEmpty) {
      final query = _searchQuery.toLowerCase();
      filtered = filtered
          .where((p) =>
              p.name.toLowerCase().contains(query) ||
              (p.brand?.toLowerCase().contains(query) ?? false))
          .toList();
    }
    return filtered;
  }

  Future<void> loadProducts() async {
    _isLoading = true;
    notifyListeners();
    try {
      final response = await _apiClient.get(Endpoints.products);
      final items = response['items'] ?? response;
      _products = (items as List).map((p) => Product.fromJson(p)).toList();
      _error = null;
    } on ApiException catch (e) {
      _error = e.message;
    } catch (_) {
      _error = 'Failed to load products';
    }
    _isLoading = false;
    notifyListeners();
  }

  Future<void> loadCategories() async {
    try {
      final response = await _apiClient.get(Endpoints.productCategories);
      _categories = (response as List)
          .map((c) => ProductCategory.fromJson(c))
          .toList();
      notifyListeners();
    } catch (_) {}
  }

  Future<void> loadPromotions() async {
    try {
      final response = await _apiClient.get(Endpoints.promotions);
      _promotions = (response['items'] as List?)
              ?.map((p) => Promotion.fromJson(p))
              .toList() ??
          [];
      notifyListeners();
    } catch (_) {}
  }

  void setCategory(String category) {
    _selectedCategory = category;
    notifyListeners();
  }

  void search(String query) {
    _searchQuery = query;
    notifyListeners();
  }

  void clearSearch() {
    _searchQuery = '';
    notifyListeners();
  }

  Product? getProductById(int id) {
    try {
      return _products.firstWhere((p) => p.id == id);
    } catch (_) {
      return null;
    }
  }
}
