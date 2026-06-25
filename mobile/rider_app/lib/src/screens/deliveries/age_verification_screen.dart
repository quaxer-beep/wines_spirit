import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shared_core/shared_core.dart';
import '../../providers/rider_delivery_provider.dart';

class AgeVerificationScreen extends StatefulWidget {
  final RiderDelivery delivery;

  const AgeVerificationScreen({super.key, required this.delivery});

  @override
  State<AgeVerificationScreen> createState() => _AgeVerificationScreenState();
}

class _AgeVerificationScreenState extends State<AgeVerificationScreen> {
  String _selectedDocType = 'National ID';
  final _docNumberController = TextEditingController();
  bool _isVerifying = false;

  @override
  void dispose() {
    _docNumberController.dispose();
    super.dispose();
  }

  Future<void> _verify() async {
    final docNum = _docNumberController.text.trim();
    if (docNum.isEmpty) return;

    setState(() => _isVerifying = true);

    final provider = context.read<RiderDeliveryProvider>();
    final ok = await provider.verifyAge(
      widget.delivery.id,
      documentType: _selectedDocType,
      documentNumber: docNum,
    );

    if (!mounted) return;

    setState(() => _isVerifying = false);

    if (ok) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Age verified successfully')),
      );
      Navigator.pop(context, true);
    }
  }

  @override
  Widget build(BuildContext context) {
    final delivery = widget.delivery;
    final provider = context.watch<RiderDeliveryProvider>();

    return Scaffold(
      appBar: AppBar(
        title: const Text('Age Verification'),
      ),
      body: LoadingOverlay(
        isLoading: _isVerifying || provider.isLoading,
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Delivery Info', style: AppTextStyles.titleMedium),
                      const SizedBox(height: 12),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text('Order #', style: AppTextStyles.bodySmall),
                          Text('#${delivery.orderId}', style: AppTextStyles.bodyMedium),
                        ],
                      ),
                      const SizedBox(height: 8),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text('Customer', style: AppTextStyles.bodySmall),
                          Text(delivery.customerName ?? 'N/A', style: AppTextStyles.bodyMedium),
                        ],
                      ),
                      const SizedBox(height: 8),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text('Address', style: AppTextStyles.bodySmall),
                          Flexible(
                            child: Text(
                              delivery.address,
                              style: AppTextStyles.bodyMedium,
                              textAlign: TextAlign.end,
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 24),
              Text('Customer Age Verification', style: AppTextStyles.titleLarge),
              const SizedBox(height: 8),
              Text(
                'Please verify the customer\'s identity and age by checking their official document.',
                style: AppTextStyles.bodySmall,
              ),
              const SizedBox(height: 24),
              Text('Document Type', style: AppTextStyles.labelMedium),
              const SizedBox(height: 8),
              DropdownButtonFormField<String>(
                value: _selectedDocType,
                items: const [
                  DropdownMenuItem(value: 'National ID', child: Text('National ID')),
                  DropdownMenuItem(value: 'Passport', child: Text('Passport')),
                  DropdownMenuItem(value: 'Alien Card', child: Text('Alien Card')),
                ],
                onChanged: (v) {
                  if (v != null) setState(() => _selectedDocType = v);
                },
                decoration: const InputDecoration(
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 16),
              Text('Document Number', style: AppTextStyles.labelMedium),
              const SizedBox(height: 8),
              TextField(
                controller: _docNumberController,
                decoration: const InputDecoration(
                  border: OutlineInputBorder(),
                  hintText: 'Enter document number',
                ),
              ),
              const SizedBox(height: 32),
              SizedBox(
                width: double.infinity,
                height: 52,
                child: ElevatedButton.icon(
                  onPressed: _isVerifying ? null : _verify,
                  icon: const Icon(Icons.verified_user),
                  label: Text(_isVerifying ? 'Verifying...' : 'Confirm Verification'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.success,
                    foregroundColor: Colors.white,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
