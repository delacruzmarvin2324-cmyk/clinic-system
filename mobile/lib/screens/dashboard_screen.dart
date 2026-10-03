import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../clinic_api.dart';
import '../theme.dart';
import '../widgets/brand_logo.dart';
import 'admin_screen.dart';
import 'booking_screen.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({
    super.key,
    required this.api,
    required this.user,
    required this.onSignOut,
  });

  final ClinicApi api;
  final Map<String, dynamic> user;
  final Future<void> Function() onSignOut;

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  late Future<Map<String, dynamic>> _dashboard;
  String _filter = 'All';
  bool _actionBusy = false;

  String get _role => widget.user['role']?.toString() ?? 'patient';
  bool get _isDoctor => _role == 'doctor';
  bool get _isPatient => _role == 'patient';
  bool get _isAdmin => _role == 'admin';

  @override
  void initState() {
    super.initState();
    _dashboard = widget.api.dashboard();
  }

  Future<void> _refresh() async {
    setState(() => _dashboard = widget.api.dashboard());
    await _dashboard;
  }

  Future<void> _openBooking() async {
    final booked = await Navigator.of(context).push<bool>(
      MaterialPageRoute(builder: (_) => BookingScreen(api: widget.api)),
    );
    if (booked == true) _refresh();
  }

  Future<void> _openAdmin() async {
    await Navigator.of(context).push<void>(
      MaterialPageRoute(builder: (_) => AdminScreen(api: widget.api)),
    );
  }

  Future<void> _decide(Map<String, dynamic> appointment, String action) async {
    String reason = '';
    if (action == 'reject') {
      final controller = TextEditingController();
      final result = await showDialog<String>(
        context: context,
        builder: (context) => AlertDialog(
          title: const Text('Reject appointment'),
          content: TextField(
            controller: controller,
            maxLines: 3,
            decoration: const InputDecoration(labelText: 'Reason (optional)'),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Cancel'),
            ),
            FilledButton(
              onPressed: () => Navigator.pop(context, controller.text.trim()),
              child: const Text('Reject'),
            ),
          ],
        ),
      );
      controller.dispose();
      if (result == null) return;
      reason = result;
    }
    setState(() => _actionBusy = true);
    try {
      await widget.api.decideAppointment(
        appointment['id'] as int,
        action,
        reason: reason,
      );
      await _refresh();
      if (mounted) {
        _showMessage(
          action == 'accept'
              ? 'Appointment accepted.'
              : 'Appointment rejected.',
        );
      }
    } on ApiException catch (error) {
      if (mounted) _showMessage(error.message);
    } finally {
      if (mounted) setState(() => _actionBusy = false);
    }
  }

  void _showMessage(String text) {
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(text)));
  }

  @override
  Widget build(BuildContext context) {
    final firstName = (widget.user['first_name'] as String?)?.trim();
    final greetingName = firstName == null || firstName.isEmpty
        ? widget.user['username']
        : firstName;
    final colors = Theme.of(context).colorScheme;
    final compact = MediaQuery.sizeOf(context).width < 560;
    return Scaffold(
      appBar: AppBar(
        titleSpacing: 20,
        title: const BrandLogo(compact: true),
        actions: [
          if (!compact)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12),
              child: Center(
                child: Text(
                  'Hello, $greetingName',
                  style: const TextStyle(
                    color: ClinicColors.navy,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
            ),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 12),
            child: Text(
              'Dashboard',
              style: TextStyle(
                color: ClinicColors.navy,
                fontWeight: FontWeight.w700,
                fontSize: compact ? 12 : 14,
              ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 12),
            child: FilledButton(
              onPressed: widget.onSignOut,
              style: FilledButton.styleFrom(
                minimumSize: Size(compact ? 74 : 90, 36),
                padding: const EdgeInsets.symmetric(horizontal: 12),
              ),
              child: Text(compact ? 'Logout' : 'Logout'),
            ),
          ),
        ],
      ),
      floatingActionButton: _isPatient
          ? FloatingActionButton.extended(
              onPressed: _openBooking,
              icon: const Icon(Icons.add),
              label: const Text('Book appointment'),
            )
          : null,
      body: RefreshIndicator(
        onRefresh: _refresh,
        child: FutureBuilder<Map<String, dynamic>>(
          future: _dashboard,
          builder: (context, snapshot) {
            if (snapshot.hasError) {
              return ListView(
                children: [
                  const SizedBox(height: 150),
                  Center(
                    child: Padding(
                      padding: const EdgeInsets.all(24),
                      child: Column(
                        children: [
                          const Icon(Icons.cloud_off_outlined, size: 42),
                          const SizedBox(height: 12),
                          Text(
                            snapshot.error is ApiException
                                ? (snapshot.error as ApiException).message
                                : 'Could not load appointments.',
                          ),
                          TextButton(
                            onPressed: _refresh,
                            child: const Text('Retry'),
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              );
            }
            if (!snapshot.hasData) {
              return const Center(child: CircularProgressIndicator());
            }
            final data = snapshot.data!;
            final all = (data['appointments'] as List<dynamic>)
                .map((item) => Map<String, dynamic>.from(item as Map))
                .toList();
            final today = DateUtils.dateOnly(DateTime.now());
            final appointments = all.where((item) {
              if (_filter == 'Upcoming') {
                final appointmentDate = DateTime.tryParse(
                  item['date']?.toString() ?? '',
                );
                return appointmentDate != null &&
                    !DateUtils.dateOnly(appointmentDate).isBefore(today) &&
                    ['Pending', 'Scheduled'].contains(item['status']);
              }
              if (_filter == 'Completed') return item['status'] == 'Completed';
              return true;
            }).toList();
            final upcomingCount = data['upcoming_appointments'] as int? ?? 0;
            return ListView(
              padding: const EdgeInsets.fromLTRB(20, 18, 20, 100),
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 22,
                    vertical: 20,
                  ),
                  decoration: BoxDecoration(
                    gradient: const LinearGradient(
                      colors: [Color(0xFFE2FAF8), Color(0xFFD5F4F4)],
                    ),
                    borderRadius: BorderRadius.circular(15),
                    border: Border.all(color: const Color(0xFFBDEBEA)),
                  ),
                  child: Row(
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Welcome back, ${_isDoctor ? 'Dr. ' : ''}$greetingName',
                              style: const TextStyle(
                                color: ClinicColors.navy,
                                fontSize: 20,
                                fontWeight: FontWeight.w800,
                              ),
                            ),
                            const SizedBox(height: 5),
                            Text(
                              _isDoctor
                                  ? 'Keep track of appointments and patient follow-up needs in one place.'
                                  : 'Your care schedule and follow-up needs, all in one place.',
                              style: const TextStyle(
                                color: ClinicColors.muted,
                                fontSize: 13,
                              ),
                            ),
                          ],
                        ),
                      ),
                      if (!compact) ...[
                        const SizedBox(width: 16),
                        Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 13,
                            vertical: 8,
                          ),
                          decoration: BoxDecoration(
                            color: const Color(0xFFEAF1FF),
                            borderRadius: BorderRadius.circular(20),
                          ),
                          child: Text(
                            '${_role[0].toUpperCase()}${_role.substring(1)} Account',
                            style: const TextStyle(
                              color: Color(0xFF3659B7),
                              fontSize: 12,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
                const SizedBox(height: 22),
                Text(
                  'Appointment overview',
                  style: Theme.of(context).textTheme.titleLarge
                      ?.copyWith(fontSize: 18, fontWeight: FontWeight.w800),
                ),
                const SizedBox(height: 4),
                Text(
                  'A clear snapshot of upcoming care and follow-up risk.',
                  style: TextStyle(color: colors.onSurfaceVariant),
                ),
                const SizedBox(height: 16),
                Row(
                  children: [
                    Expanded(
                      child: _StatBlock(
                        label: 'Appointments',
                        value: '${data['total_appointments'] ?? 0}',
                        icon: Icons.event_note_outlined,
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: _StatBlock(
                        label: 'Upcoming consults',
                        value: '$upcomingCount',
                        icon: Icons.calendar_month_outlined,
                        accent: true,
                      ),
                    ),
                  ],
                ),
                if (_isAdmin) ...[
                  const SizedBox(height: 12),
                  OutlinedButton.icon(
                    onPressed: _openAdmin,
                    icon: const Icon(Icons.manage_accounts_outlined),
                    label: const Text('Manage clinic records'),
                    style: OutlinedButton.styleFrom(
                      alignment: Alignment.centerLeft,
                      minimumSize: const Size.fromHeight(48),
                    ),
                  ),
                ],
                const SizedBox(height: 28),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      'Appointments',
                      style: Theme.of(context).textTheme.titleLarge
                          ?.copyWith(fontWeight: FontWeight.w700),
                    ),
                    Text(
                      '${appointments.length} shown',
                      style: TextStyle(
                        color: colors.onSurfaceVariant,
                        fontSize: 13,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                SegmentedButton<String>(
                  segments: const [
                    ButtonSegment(value: 'All', label: Text('All')),
                    ButtonSegment(value: 'Upcoming', label: Text('Upcoming')),
                    ButtonSegment(value: 'Completed', label: Text('Completed')),
                  ],
                  selected: {_filter},
                  onSelectionChanged: (value) =>
                      setState(() => _filter = value.first),
                  showSelectedIcon: false,
                ),
                const SizedBox(height: 14),
                if (appointments.isEmpty)
                  _EmptyState(isPatient: _isPatient, onBook: _openBooking)
                else
                  ...appointments.map(
                    (appointment) => Padding(
                      padding: const EdgeInsets.only(bottom: 12),
                      child: _AppointmentTile(
                        appointment: appointment,
                        isDoctor: _isDoctor,
                        busy: _actionBusy,
                        onAccept: () => _decide(appointment, 'accept'),
                        onReject: () => _decide(appointment, 'reject'),
                      ),
                    ),
                  ),
              ],
            );
          },
        ),
      ),
    );
  }
}

class _StatBlock extends StatelessWidget {
  const _StatBlock({
    required this.label,
    required this.value,
    required this.icon,
    this.accent = false,
  });
  final String label;
  final String value;
  final IconData icon;
  final bool accent;

  @override
  Widget build(BuildContext context) {
    final color = accent ? ClinicColors.cyan : const Color(0xFF09B6C9);
    return ClipRRect(
      borderRadius: BorderRadius.circular(12),
      child: Container(
        decoration: BoxDecoration(
          color: Colors.white,
          border: Border.all(color: ClinicColors.line),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(height: 5, color: color),
            Padding(
              padding: const EdgeInsets.fromLTRB(19, 15, 19, 17),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    label.toUpperCase(),
                    style: const TextStyle(
                      color: ClinicColors.muted,
                      fontSize: 11,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      Text(
                        value,
                        style: const TextStyle(
                          color: ClinicColors.navy,
                          fontSize: 31,
                          height: 1,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                      const Spacer(),
                      Icon(icon, color: color, size: 22),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _AppointmentTile extends StatelessWidget {
  const _AppointmentTile({
    required this.appointment,
    required this.isDoctor,
    required this.busy,
    required this.onAccept,
    required this.onReject,
  });
  final Map<String, dynamic> appointment;
  final bool isDoctor;
  final bool busy;
  final VoidCallback onAccept;
  final VoidCallback onReject;

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    final status = appointment['status']?.toString() ?? 'Pending';
    final risk = appointment['risk_level']?.toString() ?? 'Unavailable';
    final probability = appointment['risk_probability'];
    final date = DateTime.tryParse(appointment['date']?.toString() ?? '');
    final dateLabel = date == null
        ? appointment['date'].toString()
        : DateFormat('EEE, d MMM yyyy').format(date);
    final isPending = isDoctor && status == 'Pending';
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: ClinicColors.line),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 45,
                height: 45,
                decoration: BoxDecoration(
                  color: const Color(0xFFE3F8F7),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Icon(
                  Icons.medical_services_outlined,
                  color: colors.primary,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      isDoctor
                          ? appointment['patient'].toString()
                          : appointment['doctor'].toString(),
                      style: const TextStyle(
                        fontWeight: FontWeight.w700,
                        fontSize: 16,
                      ),
                    ),
                    const SizedBox(height: 3),
                    Text(
                      isDoctor
                          ? appointment['appointment_type'].toString()
                          : appointment['specialty'].toString(),
                      style: TextStyle(
                        color: colors.onSurfaceVariant,
                        fontSize: 13,
                      ),
                    ),
                  ],
                ),
              ),
              _StatusLabel(status: status),
            ],
          ),
          const SizedBox(height: 15),
          Wrap(
            spacing: 18,
            runSpacing: 8,
            children: [
              _Meta(icon: Icons.calendar_today_outlined, text: dateLabel),
              _Meta(
                icon: Icons.schedule_outlined,
                text: appointment['time'].toString(),
              ),
            ],
          ),
          if (probability != null || risk != 'Unavailable') ...[
            const SizedBox(height: 12),
            Row(
              children: [
                Icon(
                  Icons.insights_outlined,
                  size: 17,
                  color: _riskColor(risk),
                ),
                const SizedBox(width: 6),
                Text(
                  'No-show risk: ${probability == null ? 'n/a' : '${(probability * 100).round()}%'} · $risk',
                  style: TextStyle(
                    color: _riskColor(risk),
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
          ],
          if (status == 'Rejected' &&
              (appointment['rejection_reason'] as String? ?? '')
                  .isNotEmpty) ...[
            const SizedBox(height: 9),
            Text(
              'Reason: ${appointment['rejection_reason']}',
              style: TextStyle(color: colors.error, fontSize: 13),
            ),
          ],
          if (isPending) ...[
            const Divider(height: 26),
            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                OutlinedButton(
                  onPressed: busy ? null : onReject,
                  child: const Text('Reject'),
                ),
                const SizedBox(width: 8),
                FilledButton.icon(
                  onPressed: busy ? null : onAccept,
                  icon: const Icon(Icons.check, size: 18),
                  label: const Text('Accept'),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }

  Color _riskColor(String risk) {
    if (risk == 'High risk') return ClinicColors.red;
    if (risk == 'Medium risk') return ClinicColors.amber;
    return ClinicColors.green;
  }
}

class _StatusLabel extends StatelessWidget {
  const _StatusLabel({required this.status});
  final String status;

  @override
  Widget build(BuildContext context) {
    final color = switch (status) {
      'Scheduled' || 'Completed' => ClinicColors.green,
      'Rejected' || 'Cancelled' => ClinicColors.red,
      _ => ClinicColors.amber,
    };
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(5),
      ),
      child: Text(
        status,
        style: TextStyle(
          color: color,
          fontSize: 11,
          fontWeight: FontWeight.w700,
        ),
      ),
    );
  }
}

class _Meta extends StatelessWidget {
  const _Meta({required this.icon, required this.text});
  final IconData icon;
  final String text;

  @override
  Widget build(BuildContext context) => Row(
    mainAxisSize: MainAxisSize.min,
    children: [
      Icon(icon, size: 15, color: const Color(0xFF65736E)),
      const SizedBox(width: 6),
      Text(
        text,
        style: const TextStyle(fontSize: 13, color: Color(0xFF46544F)),
      ),
    ],
  );
}

class _EmptyState extends StatelessWidget {
  const _EmptyState({required this.isPatient, required this.onBook});
  final bool isPatient;
  final VoidCallback onBook;

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 42),
    child: Column(
      children: [
        const Icon(
          Icons.event_busy_outlined,
          size: 40,
          color: Color(0xFF84918C),
        ),
        const SizedBox(height: 10),
        const Text(
          'No appointments found',
          style: TextStyle(fontWeight: FontWeight.w700),
        ),
        const SizedBox(height: 5),
        Text(
          isPatient
              ? 'Your upcoming care will appear here.'
              : 'Appointments assigned to you will appear here.',
          textAlign: TextAlign.center,
          style: const TextStyle(color: Color(0xFF65736E)),
        ),
        if (isPatient) ...[
          const SizedBox(height: 13),
          OutlinedButton.icon(
            onPressed: onBook,
            icon: const Icon(Icons.add),
            label: const Text('Book appointment'),
          ),
        ],
      ],
    ),
  );
}
