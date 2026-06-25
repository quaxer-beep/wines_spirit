class Validators {
  Validators._();

  static String? required(String? value, [String? fieldName]) {
    if (value == null || value.trim().isEmpty) {
      return '${fieldName ?? 'This field'} is required';
    }
    return null;
  }

  static String? phone(String? value) {
    if (value == null || value.isEmpty) return 'Phone number is required';
    final cleaned = value.replaceAll(RegExp(r'[\s\-\(\)\+]'), '');
    if (cleaned.length < 9) return 'Invalid phone number';
    if (!RegExp(r'^(0|254|7|1)\d{8,12}$').hasMatch(cleaned)) {
      return 'Enter a valid Kenyan phone number';
    }
    return null;
  }

  static String? email(String? value) {
    if (value == null || value.isEmpty) return null;
    if (!RegExp(r'^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$').hasMatch(value)) {
      return 'Enter a valid email address';
    }
    return null;
  }

  static String? password(String? value) {
    if (value == null || value.isEmpty) return 'Password is required';
    if (value.length < 6) return 'Password must be at least 6 characters';
    if (value.length > 128) return 'Password is too long';
    return null;
  }

  static String? confirmPassword(String? value, String password) {
    if (value == null || value.isEmpty) return 'Please confirm your password';
    if (value != password) return 'Passwords do not match';
    return null;
  }

  static String? positiveNumber(String? value, [String? fieldName]) {
    if (value == null || value.isEmpty) return '${fieldName ?? 'Value'} is required';
    final num = double.tryParse(value);
    if (num == null || num <= 0) return 'Enter a valid positive number';
    return null;
  }

  static String? integer(String? value, [String? fieldName]) {
    if (value == null || value.isEmpty) return '${fieldName ?? 'Value'} is required';
    if (int.tryParse(value) == null) return 'Enter a valid whole number';
    return null;
  }

  static String? age(String? value) {
    if (value == null || value.isEmpty) return 'Date of birth is required';
    try {
      final dob = DateTime.parse(value);
      final now = DateTime.now();
      final age = now.year - dob.year;
      if (age < 18) return 'You must be 18 or older';
      if (age > 120) return 'Invalid date of birth';
    } catch (_) {
      return 'Invalid date format';
    }
    return null;
  }

  static String? nationalId(String? value) {
    if (value == null || value.isEmpty) return 'National ID is required';
    final cleaned = value.trim();
    if (cleaned.length < 6 || cleaned.length > 12) return 'Invalid ID number';
    if (!RegExp(r'^\d+$').hasMatch(cleaned)) return 'ID must contain only numbers';
    return null;
  }

  static String? rating(int? value) {
    if (value == null || value < 1 || value > 5) return 'Rating must be between 1 and 5';
    return null;
  }
}
