import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shared_core/shared_core.dart';
import '../../providers/rider_incident_provider.dart';
import '../../providers/rider_location_provider.dart';

class IncidentReportScreen extends StatefulWidget {
  final int? deliveryId;

  const IncidentReportScreen({super.key, this.deliveryId});

  @override
  State<IncidentReportScreen> createState() => _IncidentReportScreenState();
}

class _IncidentReportScreenState extends State<IncidentReportScreen> {
  final _formKey = GlobalKey<FormState>();
  final _descriptionController = TextEditingController();
  String _selectedType = 'customer_not_available';
  bool _photoAttached = false;

  final List<Map<String, dynamic>> _incidentTypes = [
    {'value': 'traffic', 'label': 'Traffic'},
    {'value': 'invalid_address', 'label': 'Wrong Address'},
    {'value': 'product_damage', 'label': 'Damaged Items'},
    {'value': 'customer_not_available', 'label': 'Customer Unavailable'},
    {'value': 'vehicle_issue', 'label': 'Vehicle Issue'},
    {'value': 'other', 'label': 'Other'},
  ];

  @override
  void initState() {
    super.initState();
    if (widget.deliveryId == null) {
      context.read<RiderIncidentProvider>().fetchIncidents();
    }
  }

  @override
  void dispose() {
    _descriptionController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    final location = context.read<RiderLocationProvider>().currentLocation;
    final provider = context.read<RiderIncidentProvider>();
    final success = await provider.reportIncident(
      deliveryId: widget.deliveryId ?? 0,
      type: _selectedType,
      description: _descriptionController.text.trim(),
      latitude: location?.latitude,
      longitude: location?.longitude,
    );
    if (success && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Incident reported successfully')),
      );
      Navigator.pop(context);
    }
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<RiderIncidentProvider>();
    return Scaffold(
      appBar: AppBar(
        title: const Text('Report Incident'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Incident Details', style: AppTextStyles.headlineMedium),
              const SizedBox(height: 20),
              DropdownButtonFormField<String>(
                value: _selectedType,
                decoration: const InputDecoration(
                  labelText: 'Incident Type',
                  prefixIcon: Icon(Icons.category_outlined),
                ),
                items: _incidentTypes
                    .map((t) => DropdownMenuItem(
                          value: t['value'],
                          child: Text(t['label']),
                        ))
                    .toList(),
                onChanged: (v) {
                  if (v != null) setState(() => _selectedType = v);
                },
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _descriptionController,
                maxLines: 5,
                decoration: const InputDecoration(
                  labelText: 'Description',
                  hintText: 'Describe the incident in detail...',
                  alignLabelWithHint: true,
                ),
                validator: (v) {
                  if (v == null || v.trim().isEmpty) {
                    return 'Please provide a description';
                  }
                  return null;
                },
              ),
              const SizedBox(height: 16),
              Row(
                children: [
                  OutlinedButton.icon(
                    onPressed: () {
                      setState(() => _photoAttached = !_photoAttached);
                    },
                    icon: Icon(
                      _photoAttached ? Icons.check : Icons.camera_alt_outlined,
                    ),
                    label: Text(_photoAttached ? 'Photo Added' : 'Add Photo'),
                  ),
                  const SizedBox(width: 12),
                  if (_photoAttached)
                    Container(
                      width: 60,
                      height: 60,
                      decoration: BoxDecoration(
                        color: AppColors.surfaceVariant,
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Icon(Icons.image,
                          color: AppColors.textSecondary),
                    ),
                ],
              ),
              const SizedBox(height: 8),
              Row(
                children: [
                  Icon(Icons.location_on,
                      size: 14, color: AppColors.textSecondary),
                  const SizedBox(width: 4),
                  Text(
                    'Location will be auto-captured',
                    style: AppTextStyles.caption,
                  ),
                ],
              ),
              if (provider.error != null) ...[
                const SizedBox(height: 16),
                Text(provider.error!, style: AppTextStyles.error),
              ],
              const SizedBox(height: 24),
              LoadingButton(
                isLoading: provider.isLoading,
                label: 'Submit Report',
                onPressed: _submit,
              ),
              if (widget.deliveryId == null) ...[
                const SizedBox(height: 32),
                Text('Recent Incidents', style: AppTextStyles.titleLarge),
                const SizedBox(height: 8),
                _buildIncidentList(provider),
              ],
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildIncidentList(RiderIncidentProvider provider) {
    if (provider.isLoading) {
      return const Center(child: CircularProgressIndicator());
    }
    if (provider.incidents.isEmpty) {
      return Padding(
        padding: const EdgeInsets.all(24),
        child: Text(
          'No incidents reported',
          style: AppTextStyles.bodySmall,
          textAlign: TextAlign.center,
        ),
      );
    }
    return SizedBox(
      height: 300,
      child: ListView.builder(
        itemCount: provider.incidents.length,
        itemBuilder: (context, index) {
          final incident = provider.incidents[index];
          return ListTile(
            leading: Icon(
              incident.isOpen ? Icons.error_outline : Icons.check_circle,
              color: incident.isOpen ? AppColors.error : AppColors.success,
            ),
            title: Text(incident.incidentTypeLabel,
                style: AppTextStyles.bodyMedium),
            subtitle: Text(
              incident.description ?? '',
              style: AppTextStyles.caption,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
            trailing: Text(
              incident.resolutionStatus.toUpperCase(),
              style: AppTextStyles.caption,
            ),
          );
        },
      ),
    );
  }
}
