class Customer {
  final int id;
  final String fullName;
  final String phone;
  final String? email;
  final String role;
  final bool ageVerified;
  final String status;
  final DateTime? dateOfBirth;
  final String ageVerificationStatus;
  final DateTime? verificationTimestamp;
  final bool isLegalAge;
  final String? registrationDate;

  Customer({
    required this.id,
    required this.fullName,
    required this.phone,
    this.email,
    this.role = 'customer',
    this.ageVerified = false,
    this.status = 'active',
    this.dateOfBirth,
    this.ageVerificationStatus = 'unverified',
    this.verificationTimestamp,
    this.isLegalAge = false,
    this.registrationDate,
  });

  factory Customer.fromJson(Map<String, dynamic> json) {
    return Customer(
      id: json['id'],
      fullName: json['full_name'] ?? '',
      phone: json['phone'] ?? '',
      email: json['email'],
      role: json['role'] ?? 'customer',
      ageVerified: json['age_verified'] ?? false,
      status: json['status'] ?? 'active',
      dateOfBirth: json['date_of_birth'] != null ? DateTime.parse(json['date_of_birth'] as String) : null,
      ageVerificationStatus: json['age_verification_status'] ?? 'unverified',
      verificationTimestamp: json['verification_timestamp'] != null ? DateTime.parse(json['verification_timestamp'] as String) : null,
      isLegalAge: json['is_legal_age'] ?? false,
      registrationDate: json['registration_date'],
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'full_name': fullName,
        'phone': phone,
        'email': email,
        'role': role,
        'age_verified': ageVerified,
        'status': status,
        'date_of_birth': dateOfBirth?.toIso8601String(),
        'age_verification_status': ageVerificationStatus,
        'verification_timestamp': verificationTimestamp?.toIso8601String(),
        'is_legal_age': isLegalAge,
      };

  bool get isAdmin => role == 'admin' || role == 'manager';
  bool get isRider => role == 'rider';
  bool get isCustomer => role == 'customer';

  String get initials {
    final parts = fullName.split(' ');
    if (parts.length >= 2) {
      return '${parts[0][0]}${parts[1][0]}'.toUpperCase();
    }
    return fullName.isNotEmpty ? fullName[0].toUpperCase() : '?';
  }
}
