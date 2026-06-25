class LoyaltyAccount {
  final int id;
  final int customerId;
  final int pointsEarned;
  final int pointsRedeemed;
  final int pointsExpired;
  final int currentBalance;

  LoyaltyAccount({
    required this.id,
    required this.customerId,
    this.pointsEarned = 0,
    this.pointsRedeemed = 0,
    this.pointsExpired = 0,
    this.currentBalance = 0,
  });

  factory LoyaltyAccount.fromJson(Map<String, dynamic> json) {
    return LoyaltyAccount(
      id: json['id'],
      customerId: json['customer_id'],
      pointsEarned: json['points_earned'] ?? 0,
      pointsRedeemed: json['points_redeemed'] ?? 0,
      pointsExpired: json['points_expired'] ?? 0,
      currentBalance: json['current_balance'] ?? 0,
    );
  }

  double get approximateValue => currentBalance * 0.05;
}

class LoyaltyTransaction {
  final int id;
  final String transactionType;
  final int points;
  final String? referenceType;
  final int? referenceId;
  final String? description;
  final String? expiryDate;
  final String createdAt;

  LoyaltyTransaction({
    required this.id,
    required this.transactionType,
    required this.points,
    this.referenceType,
    this.referenceId,
    this.description,
    this.expiryDate,
    required this.createdAt,
  });

  factory LoyaltyTransaction.fromJson(Map<String, dynamic> json) {
    return LoyaltyTransaction(
      id: json['id'],
      transactionType: json['transaction_type'] ?? '',
      points: json['points'] ?? 0,
      referenceType: json['reference_type'],
      referenceId: json['reference_id'],
      description: json['description'],
      expiryDate: json['expiry_date'],
      createdAt: json['created_at'] ?? '',
    );
  }

  bool get isEarned => transactionType == 'earn';
  bool get isRedeemed => transactionType == 'redeem';
  bool get isExpired => transactionType == 'expire';
}
