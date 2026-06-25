import 'package:flutter/material.dart';
import 'package:shared_core/shared_core.dart';
import 'status_badge.dart';

class IncidentCard extends StatefulWidget {
  final DeliveryIncident incident;
  final VoidCallback? onTap;

  const IncidentCard({
    super.key,
    required this.incident,
    this.onTap,
  });

  @override
  State<IncidentCard> createState() => _IncidentCardState();
}

class _IncidentCardState extends State<IncidentCard> {
  bool _expanded = false;

  IconData get _typeIcon {
    switch (widget.incident.incidentType) {
      case 'traffic':
        return Icons.traffic;
      case 'invalid_address':
      case 'wrong_address':
        return Icons.location_off;
      case 'product_damage':
      case 'damaged_items':
        return Icons.inventory_2_outlined;
      case 'customer_not_available':
      case 'customer_unavailable':
        return Icons.person_off_outlined;
      case 'vehicle_issue':
        return Icons.time_to_leave_outlined;
      default:
        return Icons.report_problem_outlined;
    }
  }

  String get _formattedDate {
    try {
      final dt = DateTime.parse(widget.incident.createdAt);
      return '${dt.day}/${dt.month}/${dt.year}';
    } catch (_) {
      return widget.incident.createdAt;
    }
  }

  @override
  Widget build(BuildContext context) {
    final incident = widget.incident;
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      child: InkWell(
        onTap: () {
          setState(() => _expanded = !_expanded);
          widget.onTap?.call();
        },
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Icon(_typeIcon, size: 28, color: AppColors.primary),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          incident.incidentTypeLabel,
                          style: AppTextStyles.titleMedium,
                        ),
                        const SizedBox(height: 2),
                        Text(
                          incident.description ?? 'No description',
                          style: AppTextStyles.bodySmall,
                          maxLines: _expanded ? null : 2,
                          overflow: _expanded
                              ? TextOverflow.visible
                              : TextOverflow.ellipsis,
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 8),
                  StatusBadge(status: incident.resolutionStatus),
                ],
              ),
              const SizedBox(height: 8),
              Row(
                children: [
                  Icon(Icons.calendar_today,
                      size: 12, color: AppColors.textSecondary),
                  const SizedBox(width: 4),
                  Text(_formattedDate, style: AppTextStyles.caption),
                  const SizedBox(width: 16),
                  Icon(Icons.production_quantity_limits,
                      size: 12, color: AppColors.textSecondary),
                  const SizedBox(width: 4),
                  Text('Delivery #${incident.deliveryId}',
                      style: AppTextStyles.caption),
                  const Spacer(),
                  Icon(
                    _expanded
                        ? Icons.expand_less
                        : Icons.expand_more,
                    size: 20,
                    color: AppColors.textSecondary,
                  ),
                ],
              ),
              if (_expanded &&
                  incident.resolutionNotes != null &&
                  incident.resolutionNotes!.isNotEmpty) ...[
                const Divider(height: 16),
                Text('Resolution:', style: AppTextStyles.labelMedium),
                const SizedBox(height: 4),
                Text(incident.resolutionNotes!,
                    style: AppTextStyles.bodySmall),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
