import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shared_core/shared_core.dart';
import '../../providers/rider_incident_provider.dart';
import '../../widgets/incident_card.dart';

class IncidentListScreen extends StatefulWidget {
  const IncidentListScreen({super.key});

  @override
  State<IncidentListScreen> createState() => _IncidentListScreenState();
}

class _IncidentListScreenState extends State<IncidentListScreen> {
  @override
  void initState() {
    super.initState();
    context.read<RiderIncidentProvider>().fetchIncidents();
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<RiderIncidentProvider>();
    return Scaffold(
      appBar: AppBar(
        title: const Text('Incidents'),
      ),
      body: RefreshIndicator(
        onRefresh: () => provider.fetchIncidents(),
        child: _buildBody(provider),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {
          Navigator.pushNamed(context, '/incident-report');
        },
        child: const Icon(Icons.add),
      ),
    );
  }

  Widget _buildBody(RiderIncidentProvider provider) {
    if (provider.isLoading && provider.incidents.isEmpty) {
      return const ShimmerLoading();
    }

    if (provider.error != null && provider.incidents.isEmpty) {
      return ErrorDisplay(
        message: provider.error!,
        onRetry: () => provider.fetchIncidents(),
      );
    }

    if (provider.incidents.isEmpty) {
      return EmptyState(
        icon: Icons.report_problem_outlined,
        title: 'No Incidents',
        subtitle: 'All clear! No incidents have been reported.',
        actionLabel: 'Report Incident',
        onAction: () {
          Navigator.pushNamed(context, '/incident-report');
        },
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.only(top: 8, bottom: 88),
      itemCount: provider.incidents.length,
      itemBuilder: (context, index) {
        final incident = provider.incidents[index];
        return IncidentCard(
          incident: incident,
          onTap: () => _showIncidentDetail(incident),
        );
      },
    );
  }

  void _showIncidentDetail(DeliveryIncident incident) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder: (ctx) => Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Center(
              child: Container(
                width: 40,
                height: 4,
                decoration: BoxDecoration(
                  color: AppColors.divider,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
            ),
            const SizedBox(height: 16),
            Text(incident.incidentTypeLabel,
                style: AppTextStyles.headlineMedium),
            const SizedBox(height: 8),
            Row(
              children: [
                StatusBadge(status: incident.resolutionStatus),
                const SizedBox(width: 12),
                Text(
                  'Delivery #${incident.deliveryId}',
                  style: AppTextStyles.bodySmall,
                ),
              ],
            ),
            const SizedBox(height: 16),
            Text('Description', style: AppTextStyles.titleMedium),
            const SizedBox(height: 4),
            Text(
              incident.description ?? 'No description provided.',
              style: AppTextStyles.bodyMedium,
            ),
            if (incident.resolutionNotes != null &&
                incident.resolutionNotes!.isNotEmpty) ...[
              const SizedBox(height: 16),
              Text('Resolution', style: AppTextStyles.titleMedium),
              const SizedBox(height: 4),
              Text(incident.resolutionNotes!,
                  style: AppTextStyles.bodyMedium),
            ],
            const SizedBox(height: 16),
            Text(
              'Reported: ${incident.createdAt}',
              style: AppTextStyles.caption,
            ),
            const SizedBox(height: 24),
          ],
        ),
      ),
    );
  }
}
