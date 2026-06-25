import 'package:flutter/foundation.dart';
import 'package:shared_core/shared_core.dart';

class ExpenseProvider extends ChangeNotifier {
  final ApiClient _api;

  List<Map<String, dynamic>> _expenses = [];
  double _totalExpenses = 0;
  bool _isLoading = false;
  String? _error;

  ExpenseProvider({required ApiClient api}) : _api = api;

  List<Map<String, dynamic>> get expenses => _expenses;
  double get totalExpenses => _totalExpenses;
  bool get isLoading => _isLoading;
  String? get error => _error;

  Future<void> fetchExpenses() async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    try {
      final response = await _api.get('/expenses');
      final items = response['results'] as List<dynamic>? ?? response as List<dynamic>? ?? [];
      _expenses = items.cast<Map<String, dynamic>>();
      _totalExpenses = _expenses.fold<double>(
          0, (sum, e) => sum + ((e['amount'] as num?)?.toDouble() ?? 0));
    } on ApiException catch (e) {
      _error = e.message;
    } on NetworkException {
      _error = 'No internet connection';
    } catch (_) {
      _error = 'Failed to load expenses';
    }
    _isLoading = false;
    notifyListeners();
  }

  Future<bool> addExpense({
    required String category,
    required double amount,
    required String description,
    required DateTime date,
    String? receipt,
  }) async {
    try {
      await _api.post('/expenses', body: {
        'category': category,
        'amount': amount,
        'description': description,
        'date': date.toIso8601String().split('T')[0],
        if (receipt != null) 'receipt': receipt,
      });
      await fetchExpenses();
      return true;
    } on ApiException catch (e) {
      _error = e.message;
      notifyListeners();
      return false;
    } on NetworkException {
      _error = 'No internet connection';
      notifyListeners();
      return false;
    } catch (_) {
      _error = 'Failed to add expense';
      notifyListeners();
      return false;
    }
  }

  Future<bool> deleteExpense(int id) async {
    try {
      await _api.delete('/expenses/$id');
      await fetchExpenses();
      return true;
    } on ApiException catch (e) {
      _error = e.message;
      notifyListeners();
      return false;
    } on NetworkException {
      _error = 'No internet connection';
      notifyListeners();
      return false;
    } catch (_) {
      _error = 'Failed to delete expense';
      notifyListeners();
      return false;
    }
  }
}
