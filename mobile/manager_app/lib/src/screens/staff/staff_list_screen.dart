import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shared_core/shared_core.dart';
import '../../providers/staff_provider.dart';

class StaffListScreen extends StatefulWidget {
  const StaffListScreen({super.key});

  @override
  State<StaffListScreen> createState() => _StaffListScreenState();
}

class _StaffListScreenState extends State<StaffListScreen> {
  final _searchController = TextEditingController();
  String? _selectedRole;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<StaffProvider>().fetchStaff();
    });
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  List<Map<String, dynamic>> _filteredStaff(StaffProvider provider) {
    var items = provider.staff;
    final query = _searchController.text.trim().toLowerCase();
    if (query.isNotEmpty) {
      items = items.where((s) {
        final name = (s['full_name'] as String? ?? s['name'] as String? ?? '').toLowerCase();
        return name.contains(query);
      }).toList();
    }
    if (_selectedRole != null) {
      items = items.where((s) => s['role']?.toString() == _selectedRole).toList();
    }
    return items;
  }

  Set<String> _roles(StaffProvider provider) {
    return provider.staff
        .map((s) => s['role']?.toString() ?? 'Staff')
        .toSet();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Staff')),
      body: Consumer<StaffProvider>(
        builder: (context, provider, _) {
          if (provider.isLoading && provider.staff.isEmpty) {
            return const ShimmerLoading(itemCount: 5, itemBuilder: _shimmerItem);
          }
          if (provider.error != null && provider.staff.isEmpty) {
            return ErrorDisplay(
              message: provider.error!,
              onRetry: () => provider.fetchStaff(),
            );
          }
          final items = _filteredStaff(provider);
          return RefreshIndicator(
            onRefresh: () => provider.fetchStaff(),
            child: CustomScrollView(
              slivers: [
                SliverToBoxAdapter(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      children: [
                        TextField(
                          controller: _searchController,
                          decoration: const InputDecoration(
                            hintText: 'Search staff...',
                            prefixIcon: Icon(Icons.search),
                          ),
                          onChanged: (_) => setState(() {}),
                        ),
                        const SizedBox(height: 12),
                        SizedBox(
                          height: 36,
                          child: ListView(
                            scrollDirection: Axis.horizontal,
                            children: [
                              FilterChip(
                                label: const Text('All'),
                                selected: _selectedRole == null,
                                onSelected: (_) => setState(() => _selectedRole = null),
                              ),
                              const SizedBox(width: 8),
                              ..._roles(provider).map((role) {
                                return Padding(
                                  padding: const EdgeInsets.only(right: 8),
                                  child: FilterChip(
                                    label: Text(role),
                                    selected: _selectedRole == role,
                                    onSelected: (_) =>
                                        setState(() => _selectedRole = role),
                                  ),
                                );
                              }),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
                if (items.isEmpty)
                  const SliverFillRemaining(
                    child: EmptyState(
                      icon: Icons.people_outline,
                      title: 'No staff found',
                    ),
                  )
                else
                  SliverList(
                    delegate: SliverChildBuilderDelegate(
                      (context, index) {
                        final s = items[index];
                        return _buildStaffCard(s);
                      },
                      childCount: items.length,
                    ),
                  ),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _buildStaffCard(Map<String, dynamic> s) {
    final name = s['full_name'] as String? ?? s['name'] as String? ?? '';
    final role = s['role'] as String? ?? 'Staff';
    final isOnline = s['is_online'] as bool? ?? false;
    final shiftStart = s['shift_start'] as String? ?? '';
    final shiftEnd = s['shift_end'] as String? ?? '';

    String initials;
    final parts = name.split(' ');
    if (parts.length >= 2) {
      initials = '${parts[0][0]}${parts[1][0]}'.toUpperCase();
    } else if (name.isNotEmpty) {
      initials = name[0].toUpperCase();
    } else {
      initials = '?';
    }

    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      child: ListTile(
        onTap: () => Navigator.of(context).pushNamed(
          '/staff-detail',
          arguments: s,
        ),
        leading: Stack(
          children: [
            CircleAvatar(
              backgroundColor: AppColors.primaryLight,
              child: Text(
                initials,
                style: const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
            if (isOnline)
              Positioned(
                bottom: 0,
                right: 0,
                child: Container(
                  width: 12,
                  height: 12,
                  decoration: BoxDecoration(
                    color: AppColors.success,
                    shape: BoxShape.circle,
                    border: Border.all(color: Colors.white, width: 2),
                  ),
                ),
              ),
          ],
        ),
        title: Text(name, style: AppTextStyles.titleMedium),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const SizedBox(height: 4),
            Row(
              children: [
                Chip(
                  label: Text(role, style: AppTextStyles.caption),
                  materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                  visualDensity: VisualDensity.compact,
                  padding: EdgeInsets.zero,
                  labelPadding: const EdgeInsets.symmetric(horizontal: 8),
                ),
                const SizedBox(width: 8),
                Text(
                  isOnline ? 'Online' : 'Offline',
                  style: AppTextStyles.caption.copyWith(
                    color: isOnline ? AppColors.success : AppColors.textHint,
                  ),
                ),
              ],
            ),
            if (shiftStart.isNotEmpty || shiftEnd.isNotEmpty)
              Text(
                'Shift: ${shiftStart.isNotEmpty ? shiftStart.substring(0, 5) : '--'} - ${shiftEnd.isNotEmpty ? shiftEnd.substring(0, 5) : '--'}',
                style: AppTextStyles.caption.copyWith(color: AppColors.textHint),
              ),
          ],
        ),
        trailing: const Icon(Icons.chevron_right),
      ),
    );
  }

  static Widget _shimmerItem(int index) {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      child: Container(
        height: 72,
        padding: const EdgeInsets.all(12),
        child: Row(
          children: [
            const CircleAvatar(),
            const SizedBox(width: 12),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Container(height: 12, width: 120, color: Colors.grey[300]),
                const SizedBox(height: 6),
                Container(height: 10, width: 80, color: Colors.grey[300]),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
