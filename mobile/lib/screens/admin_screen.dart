import 'package:flutter/material.dart';

import '../clinic_api.dart';
import '../theme.dart';
import '../widgets/brand_logo.dart';

class AdminScreen extends StatefulWidget {
  const AdminScreen({super.key, required this.api});
  final ClinicApi api;

  @override
  State<AdminScreen> createState() => _AdminScreenState();
}

class _AdminScreenState extends State<AdminScreen> {
  late Future<Map<String, dynamic>> _overview;
  String _section = 'Doctors';

  @override
  void initState() {
    super.initState();
    _overview = widget.api.adminOverview();
  }

  Future<void> _refresh() async {
    setState(() => _overview = widget.api.adminOverview());
    await _overview;
  }

  Future<void> _addDoctor() async {
    final formKey = GlobalKey<FormState>();
    final fields = {
      'username': TextEditingController(),
      'password': TextEditingController(),
      'first_name': TextEditingController(),
      'last_name': TextEditingController(),
      'email': TextEditingController(),
      'specialty': TextEditingController(),
      'contact_number': TextEditingController(),
    };
    final values = await showDialog<Map<String, String>>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Add doctor'),
        content: SizedBox(
          width: 420,
          child: Form(
            key: formKey,
            child: SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  for (final entry in fields.entries)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 10),
                      child: TextFormField(
                        controller: entry.value,
                        obscureText: entry.key == 'password',
                        keyboardType: entry.key == 'email'
                            ? TextInputType.emailAddress
                            : null,
                        decoration: InputDecoration(
                          labelText: _label(entry.key),
                        ),
                        validator: (value) {
                          if (value == null || value.trim().isEmpty) {
                            return 'Required';
                          }
                          if (entry.key == 'password' && value.length < 8) {
                            return 'Use at least 8 characters';
                          }
                          if (entry.key == 'email' && !value.contains('@')) {
                            return 'Enter a valid email';
                          }
                          return null;
                        },
                      ),
                    ),
                ],
              ),
            ),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () {
              if (formKey.currentState!.validate()) {
                Navigator.pop(
                  context,
                  fields.map((key, value) => MapEntry(key, value.text.trim())),
                );
              }
            },
            child: const Text('Create doctor'),
          ),
        ],
      ),
    );
    for (final controller in fields.values) {
      controller.dispose();
    }
    if (values == null) return;
    try {
      await widget.api.createDoctor(values);
      await _refresh();
      if (mounted) _message('Doctor account created.');
    } on ApiException catch (error) {
      if (mounted) _message(error.message);
    }
  }

  String _label(String key) => switch (key) {
    'first_name' => 'First name',
    'last_name' => 'Last name',
    'contact_number' => 'Contact number',
    _ => '${key[0].toUpperCase()}${key.substring(1)}',
  };

  void _message(String text) {
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(text)));
  }

  @override
  Widget build(BuildContext context) {
    final compact = MediaQuery.sizeOf(context).width < 520;
    return Scaffold(
      appBar: AppBar(
        title: const BrandLogo(compact: true),
        actions: [
          if (!compact)
            const Padding(
              padding: EdgeInsets.only(right: 8),
              child: Center(
                child: Text(
                  'Clinic management',
                  style: TextStyle(
                    color: ClinicColors.navy,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
            ),
          IconButton(
            tooltip: 'Refresh',
            onPressed: _refresh,
            icon: const Icon(Icons.refresh),
          ),
          IconButton(
            tooltip: 'Add doctor',
            onPressed: _addDoctor,
            icon: const Icon(Icons.person_add_alt_1),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _refresh,
        child: FutureBuilder<Map<String, dynamic>>(
          future: _overview,
          builder: (context, snapshot) {
            if (snapshot.hasError) {
              return ListView(
                children: [
                  const SizedBox(height: 120),
                  Center(
                    child: Column(
                      children: [
                        const Text('Could not load clinic records.'),
                        TextButton(
                          onPressed: _refresh,
                          child: const Text('Retry'),
                        ),
                      ],
                    ),
                  ),
                ],
              );
            }
            if (!snapshot.hasData) {
              return const Center(child: CircularProgressIndicator());
            }
            final data = snapshot.data!;
            final entries =
                (data[_section.toLowerCase()] as List<dynamic>? ?? [])
                    .map((item) => Map<String, dynamic>.from(item as Map))
                    .toList();
            return ListView(
              padding: const EdgeInsets.all(20),
              children: [
                Text(
                  'Clinic records',
                  style: Theme.of(context).textTheme.headlineSmall
                      ?.copyWith(fontWeight: FontWeight.w700),
                ),
                const SizedBox(height: 16),
                SegmentedButton<String>(
                  segments: const [
                    ButtonSegment(value: 'Doctors', label: Text('Doctors')),
                    ButtonSegment(value: 'Patients', label: Text('Patients')),
                    ButtonSegment(
                      value: 'Appointments',
                      label: Text('Appointments'),
                    ),
                  ],
                  selected: {_section},
                  showSelectedIcon: false,
                  onSelectionChanged: (value) =>
                      setState(() => _section = value.first),
                ),
                const SizedBox(height: 14),
                if (entries.isEmpty)
                  const Padding(
                    padding: EdgeInsets.all(30),
                    child: Center(child: Text('No records found.')),
                  )
                else
                  ...entries.map(
                    (entry) => _RecordRow(section: _section, item: entry),
                  ),
              ],
            );
          },
        ),
      ),
    );
  }
}

class _RecordRow extends StatelessWidget {
  const _RecordRow({required this.section, required this.item});
  final String section;
  final Map<String, dynamic> item;

  @override
  Widget build(BuildContext context) {
    late final String title;
    late final String subtitle;
    late final IconData icon;
    if (section == 'Doctors') {
      title = item['doctor_name']?.toString() ?? 'Doctor';
      subtitle = '${item['specialty']} · ${item['contact_number']}';
      icon = Icons.medical_services_outlined;
    } else if (section == 'Patients') {
      title = item['name']?.toString() ?? 'Patient';
      subtitle = '${item['phone_number']} · ${item['neighbourhood']}';
      icon = Icons.person_outline;
    } else {
      title = '${item['patient']} · ${item['doctor']}';
      subtitle =
          '${item['date']} ${item['time']} · ${item['appointment_type']} · ${item['status']}';
      icon = Icons.event_note_outlined;
    }
    return Container(
      margin: const EdgeInsets.only(bottom: 9),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: ClinicColors.line),
      ),
      child: ListTile(
        leading: Icon(icon, color: Theme.of(context).colorScheme.primary),
        title: Text(title, style: const TextStyle(fontWeight: FontWeight.w600)),
        subtitle: Text(subtitle, maxLines: 2, overflow: TextOverflow.ellipsis),
      ),
    );
  }
}
