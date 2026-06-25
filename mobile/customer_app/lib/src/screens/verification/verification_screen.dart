import 'package:flutter/material.dart';
import 'package:shared_core/shared_core.dart';
import '../../providers/auth_provider.dart';

class VerificationScreen extends StatefulWidget {
  const VerificationScreen({super.key});
  @override
  State<VerificationScreen> createState() => _VerificationScreenState();
}

class _VerificationScreenState extends State<VerificationScreen> {
  DateTime? _selectedDate;
  bool _isSubmitting = false;

  Future<void> _submitAgeVerification() async {
    if (_selectedDate == null) return;
    setState(() => _isSubmitting = true);
    // Call API to save DOB
    await Future.delayed(const Duration(seconds: 1));
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Age information saved'), backgroundColor: AppColors.success),
      );
      setState(() => _isSubmitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final user = context.watch<AuthProvider>().user;
    final bool isAgeVerified = user?.ageVerified ?? false;
    final String verStatus = user?.ageVerificationStatus ?? 'unverified';

    return Scaffold(
      appBar: AppBar(title: const Text('Age Verification')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Card(
              color: isAgeVerified ? AppColors.success.withAlpha(12) : AppColors.warning.withAlpha(12),
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Row(
                  children: [
                    Icon(
                      isAgeVerified ? Icons.verified : Icons.info_outline,
                      color: isAgeVerified ? AppColors.success : AppColors.warning,
                      size: 32,
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            isAgeVerified ? 'Age Verified' : verStatus == 'pending' ? 'Verification Pending' : 'Not Verified',
                            style: AppTextStyles.titleMedium,
                          ),
                          Text(
                            isAgeVerified
                                ? 'Your age has been verified successfully'
                                : verStatus == 'pending'
                                    ? 'Your verification is being reviewed'
                                    : 'Please provide your date of birth',
                            style: AppTextStyles.bodySmall,
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
            if (!isAgeVerified) ...[
              const SizedBox(height: 24),
              Text('Personal Information', style: AppTextStyles.titleLarge),
              const SizedBox(height: 16),
              TextFormField(
                decoration: const InputDecoration(
                  labelText: 'Full Name',
                  prefixIcon: Icon(Icons.person),
                ),
                initialValue: user?.fullName ?? '',
                enabled: false,
              ),
              const SizedBox(height: 12),
              TextFormField(
                decoration: InputDecoration(
                  labelText: 'Date of Birth',
                  prefixIcon: const Icon(Icons.calendar_today),
                  suffixIcon: const Icon(Icons.date_range),
                  hintText: _selectedDate != null
                      ? '${_selectedDate!.day}/${_selectedDate!.month}/${_selectedDate!.year}'
                      : 'Select your date of birth',
                ),
                readOnly: true,
                onTap: () async {
                  final date = await showDatePicker(
                    context: context,
                    initialDate: DateTime(1990),
                    firstDate: DateTime(1900),
                    lastDate: DateTime.now(),
                  );
                  if (date != null) setState(() => _selectedDate = date);
                },
              ),
              const SizedBox(height: 8),
              // Legal age notice
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: AppColors.info.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Row(
                  children: [
                    Icon(Icons.info_outline, size: 16, color: AppColors.info),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        'You must be 18 or older to purchase alcoholic products. Your age will be verified again upon delivery.',
                        style: AppTextStyles.bodySmall?.copyWith(fontSize: 12),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 24),
              ElevatedButton(
                onPressed: _selectedDate == null || _isSubmitting ? null : _submitAgeVerification,
                child: _isSubmitting
                    ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2))
                    : const Text('Submit Date of Birth'),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
