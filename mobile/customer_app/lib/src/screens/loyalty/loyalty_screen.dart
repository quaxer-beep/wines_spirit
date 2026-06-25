import 'package:flutter/material.dart';
import 'package:shared_core/shared_core.dart';
import 'package:provider/provider.dart';
import '../../providers/auth_provider.dart';

class LoyaltyScreen extends StatefulWidget {
  const LoyaltyScreen({super.key});

  @override
  State<LoyaltyScreen> createState() => _LoyaltyScreenState();
}

class _LoyaltyScreenState extends State<LoyaltyScreen> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Loyalty Program')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Card(
              color: AppColors.primary.withAlpha(12),
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  children: [
                    const Icon(Icons.card_giftcard,
                        size: 48, color: AppColors.loyaltyGold),
                    const SizedBox(height: 12),
                    Text('Your Points', style: AppTextStyles.caption),
                    Text('0', style: AppTextStyles.displayMedium),
                    const SizedBox(height: 4),
                    Text('≈ KSh 0.00 value',
                        style: AppTextStyles.bodySmall),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),
            Text('How it works', style: AppTextStyles.titleLarge),
            const SizedBox(height: 8),
            _benefitCard(Icons.shopping_bag, 'Earn Points',
                'Earn 1 point for every KSh 1 spent'),
            _benefitCard(Icons.card_giftcard, 'Redeem Rewards',
                'Redeem points for discounts on future orders'),
            _benefitCard(Icons.star, 'Promotions',
                'Get bonus points during promotional periods'),
            const SizedBox(height: 24),
            Text('Recent Activity', style: AppTextStyles.titleLarge),
            const SizedBox(height: 8),
            const EmptyState(
              icon: Icons.history,
              title: 'No activity yet',
              subtitle: 'Start shopping to earn points',
            ),
          ],
        ),
      ),
    );
  }

  Widget _benefitCard(IconData icon, String title, String description) {
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ListTile(
        leading: Icon(icon, color: AppColors.loyaltyGold),
        title: Text(title, style: AppTextStyles.titleMedium),
        subtitle: Text(description, style: AppTextStyles.bodySmall),
      ),
    );
  }
}
