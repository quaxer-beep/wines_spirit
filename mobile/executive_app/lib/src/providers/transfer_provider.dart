import 'package:flutter/foundation.dart';
import 'package:shared_core/shared_core.dart';

class TransferProvider extends ChangeNotifier {
  final ApiClient _apiClient;

  TransferProvider({required ApiClient apiClient}) : _apiClient = apiClient;

  List<Map<String, dynamic>> _transfers = [];
  List<Map<String, dynamic>> _pendingTransfers = [];
  bool _isLoading = false;

  List<Map<String, dynamic>> get transfers => _transfers;
  List<Map<String, dynamic>> get pendingTransfers => _pendingTransfers;
  bool get isLoading => _isLoading;

  Future<void> fetchTransfers() async {
    _isLoading = true;
    notifyListeners();

    try {
      final response = await _apiClient.get(Endpoints.execTransfers);
      _transfers = List<Map<String, dynamic>>.from(response['data'] ?? []);
      _pendingTransfers = _transfers
          .where((t) => (t['status'] ?? '').toString().toLowerCase() == 'pending')
          .toList();
    } catch (_) {
      _transfers = [];
      _pendingTransfers = [];
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<bool> approveTransfer(String id) async {
    try {
      await _apiClient.post(
        Endpoints.execTransferApprove,
        body: {'transfer_id': id},
      );
      await fetchTransfers();
      return true;
    } catch (_) {
      return false;
    }
  }

  Future<bool> rejectTransfer(String id, String reason) async {
    try {
      await _apiClient.post(
        Endpoints.execTransferReject,
        body: {'transfer_id': id, 'reason': reason},
      );
      await fetchTransfers();
      return true;
    } catch (_) {
      return false;
    }
  }
}
