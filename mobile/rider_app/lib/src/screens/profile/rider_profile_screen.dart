import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shared_core/shared_core.dart';
import '../../providers/rider_auth_provider.dart';
import '../../providers/rider_delivery_provider.dart';

class RiderProfileScreen extends StatefulWidget {
  const RiderProfileScreen({super.key});

  @override
  State<RiderProfileScreen> createState() => _RiderProfileScreenState();
}

class _RiderProfileScreenState extends State<RiderProfileScreen> {
  bool _notificationsEnabled = true;
  bool _isOnline = true;

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<RiderAuthProvider>();
    final deliveryProvider = context.watch<RiderDeliveryProvider>();
    final rider = auth.user;

    final totalDeliveries = deliveryProvider.deliveries.length;
    final completedDeliveries = deliveryProvider.deliveries
        .where((d) => d.isDelivered)
        .length;
    final onTimePercentage = totalDeliveries > 0
        ? ((completedDeliveries / totalDeliveries) * 100).toInt()
        : 0;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Profile'),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () => _logout(context),
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            CircleAvatar(
              radius: 50,
              backgroundColor: AppColors.primary.withOpacity(0.1),
              child: Text(
                (rider?.name ?? 'R').substring(0, 1).toUpperCase(),
                style: TextStyle(
                  fontSize: 36,
                  color: AppColors.primary,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
            const SizedBox(height: 12),
            Text(rider?.name ?? 'Rider', style: AppTextStyles.headlineMedium),
            const SizedBox(height: 4),
            Text(rider?.email ?? '', style: AppTextStyles.bodySmall),
            const SizedBox(height: 4),
            Text(rider?.phone ?? '', style: AppTextStyles.bodySmall),
            const SizedBox(height: 24),
            _buildVehicleInfo(rider),
            const SizedBox(height: 16),
            _buildStats(totalDeliveries, completedDeliveries, onTimePercentage),
            const SizedBox(height: 16),
            _buildSettings(),
            const SizedBox(height: 24),
            SizedBox(
              width: double.infinity,
              height: 52,
              child: OutlinedButton.icon(
                onPressed: () => _logout(context),
                icon: const Icon(Icons.logout, color: AppColors.error),
                label: const Text(
                  'Sign Out',
                  style: TextStyle(color: AppColors.error),
                ),
                style: OutlinedButton.styleFrom(
                  side: const BorderSide(color: AppColors.error),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildVehicleInfo(Rider? rider) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            Icon(Icons.time_to_leave, color: AppColors.primary, size: 32),
            const SizedBox(width: 16),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Vehicle', style: AppTextStyles.caption),
                Text(rider?.vehicleType ?? 'N/A',
                    style: AppTextStyles.bodyMedium),
              ],
            ),
            const Spacer(),
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text('Plate', style: AppTextStyles.caption),
                Text(rider?.plateNumber ?? 'N/A',
                    style: AppTextStyles.bodyMedium),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStats(int total, int completed, int onTime) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceAround,
          children: [
            _buildStatItem('Deliveries', total.toString(), Icons.delivery_dining),
            _buildStatItem('Completed', completed.toString(), Icons.check_circle),
            _buildStatItem('On Time', '$onTime%', Icons.timer),
          ],
        ),
      ),
    );
  }

  Widget _buildStatItem(String label, String value, IconData icon) {
    return Column(
      children: [
        Icon(icon, color: AppColors.primary, size: 28),
        const SizedBox(height: 8),
        Text(value, style: AppTextStyles.titleLarge),
        Text(label, style: AppTextStyles.caption),
      ],
    );
  }

  Widget _buildSettings() {
    return Card(
      child: Column(
        children: [
          SwitchListTile(
            title: const Text('Online Status'),
            subtitle: const Text('Accept new delivery requests'),
            value: _isOnline,
            activeColor: AppColors.success,
            onChanged: (v) => setState(() => _isOnline = v),
          ),
          const Divider(height: 1),
          SwitchListTile(
            title: const Text('Notifications'),
            subtitle: const Text('Receive push notifications'),
            value: _notificationsEnabled,
            activeColor: AppColors.primary,
            onChanged: (v) => setState(() => _notificationsEnabled = v),
          ),
          const Divider(height: 1),
          ListTile(
            title: const Text('Biometric Login'),
            subtitle: const Text('Use fingerprint to sign in'),
            trailing: Consumer<RiderAuthProvider>(
              builder: (context, auth, _) => Switch(
                value: auth.isBiometricEnabled,
                activeColor: AppColors.primary,
                onChanged: (v) => auth.setBiometricEnabled(v),
              ),
            ),
          ),
        ],
      ),
    );
  }

  void _logout(BuildContext context) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Sign Out'),
        content: const Text('Are you sure you want to sign out?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () {
              Navigator.pop(ctx);
              context.read<RiderAuthProvider>().logout();
              Navigator.pushReplacementNamed(context, '/login');
            },
            child: const Text('Sign Out'),
          ),
        ],
      ),
    );
  }
}
