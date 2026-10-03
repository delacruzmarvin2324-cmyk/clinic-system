import 'package:flutter/material.dart';

import '../clinic_api.dart';
import '../theme.dart';
import '../widgets/brand_logo.dart';

class BookingScreen extends StatefulWidget {
  const BookingScreen({super.key, required this.api});
  final ClinicApi api;

  @override
  State<BookingScreen> createState() => _BookingScreenState();
}

class _BookingScreenState extends State<BookingScreen> {
  final _formKey = GlobalKey<FormState>();
  final _notes = TextEditingController();
  late Future<List<Map<String, dynamic>>> _doctors;
  int? _doctorId;
  String _type = 'Consultation';
  DateTime? _date;
  TimeOfDay? _time;
  bool _busy = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _doctors = widget.api.doctors();
  }

  @override
  void dispose() {
    _notes.dispose();
    super.dispose();
  }

  Future<void> _chooseDate() async {
    final today = DateUtils.dateOnly(DateTime.now());
    final date = await showDatePicker(
      context: context,
      initialDate: _date ?? today,
      firstDate: today,
      lastDate: DateTime(today.year + 2),
    );
    if (date != null) setState(() => _date = date);
  }

  Future<void> _chooseTime() async {
    final time = await showTimePicker(
      context: context,
      initialTime: _time ?? const TimeOfDay(hour: 9, minute: 0),
    );
    if (time != null) setState(() => _time = time);
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    if (_date == null || _time == null) {
      setState(() => _error = 'Choose a date and time for the appointment.');
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final result = await widget.api.bookAppointment({
        'doctor_id': _doctorId,
        'appointment_type': _type,
        'date':
            '${_date!.year.toString().padLeft(4, '0')}-${_date!.month.toString().padLeft(2, '0')}-${_date!.day.toString().padLeft(2, '0')}',
        'time':
            '${_time!.hour.toString().padLeft(2, '0')}:${_time!.minute.toString().padLeft(2, '0')}',
        'notes': _notes.text.trim(),
      });
      if (!mounted) return;
      final risk = result['risk_probability'];
      final riskLevel = result['risk_level'] ?? 'Unavailable';
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            risk == null
                ? 'Appointment requested. No-show risk is unavailable.'
                : 'Appointment requested. No-show risk: ${(risk * 100).round()}% ($riskLevel).',
          ),
        ),
      );
      Navigator.of(context).pop(true);
    } on ApiException catch (error) {
      if (mounted) setState(() => _error = error.message);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const BrandLogo(compact: true),
        actions: const [
          Padding(
            padding: EdgeInsets.only(right: 18),
            child: Center(
              child: Text(
                'Book appointment',
                style: TextStyle(
                  color: ClinicColors.navy,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ),
          ),
        ],
      ),
      body: FutureBuilder<List<Map<String, dynamic>>>(
        future: _doctors,
        builder: (context, snapshot) {
          if (snapshot.hasError) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Text('Could not load doctors.'),
                    TextButton(
                      onPressed: () =>
                          setState(() => _doctors = widget.api.doctors()),
                      child: const Text('Retry'),
                    ),
                  ],
                ),
              ),
            );
          }
          if (!snapshot.hasData) {
            return const Center(child: CircularProgressIndicator());
          }
          final doctors = snapshot.data!;
          if (doctors.isEmpty) {
            return const Center(
              child: Text('No doctors are currently available.'),
            );
          }
          _doctorId ??= doctors.first['id'] as int;
          return Center(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(20),
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 560),
                child: Container(
                  padding: const EdgeInsets.all(24),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(13),
                    border: Border.all(color: ClinicColors.line),
                    boxShadow: const [
                      BoxShadow(
                        color: Color(0x100F3550),
                        blurRadius: 20,
                        offset: Offset(0, 6),
                      ),
                    ],
                  ),
                  child: Form(
                    key: _formKey,
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Schedule a visit',
                          style: Theme.of(context).textTheme.headlineSmall
                              ?.copyWith(fontWeight: FontWeight.w700),
                        ),
                        const SizedBox(height: 6),
                        const Text(
                          'Choose a doctor and a time that works for you.',
                          style: TextStyle(color: Color(0xFF65736E)),
                        ),
                        const SizedBox(height: 24),
                        DropdownButtonFormField<int>(
                          initialValue: _doctorId,
                          decoration: const InputDecoration(
                            labelText: 'Doctor',
                          ),
                          items: doctors
                              .map(
                                (doctor) => DropdownMenuItem<int>(
                                  value: doctor['id'] as int,
                                  child: Text(
                                    '${doctor['doctor_name']} · ${doctor['specialty']}',
                                    overflow: TextOverflow.ellipsis,
                                  ),
                                ),
                              )
                              .toList(),
                          onChanged: (value) =>
                              setState(() => _doctorId = value),
                        ),
                        const SizedBox(height: 14),
                        DropdownButtonFormField<String>(
                          initialValue: _type,
                          decoration: const InputDecoration(
                            labelText: 'Appointment type',
                          ),
                          items: const [
                            DropdownMenuItem(
                              value: 'Consultation',
                              child: Text('Consultation'),
                            ),
                            DropdownMenuItem(
                              value: 'Appointment',
                              child: Text('Appointment'),
                            ),
                          ],
                          onChanged: (value) =>
                              setState(() => _type = value ?? 'Consultation'),
                        ),
                        const SizedBox(height: 14),
                        Row(
                          children: [
                            Expanded(
                              child: OutlinedButton.icon(
                                onPressed: _chooseDate,
                                icon: const Icon(Icons.calendar_month_outlined),
                                label: Text(
                                  _date == null
                                      ? 'Select date'
                                      : '${_date!.year}-${_date!.month.toString().padLeft(2, '0')}-${_date!.day.toString().padLeft(2, '0')}',
                                ),
                                style: OutlinedButton.styleFrom(
                                  minimumSize: const Size.fromHeight(52),
                                ),
                              ),
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: OutlinedButton.icon(
                                onPressed: _chooseTime,
                                icon: const Icon(Icons.schedule_outlined),
                                label: Text(
                                  _time?.format(context) ?? 'Select time',
                                ),
                                style: OutlinedButton.styleFrom(
                                  minimumSize: const Size.fromHeight(52),
                                ),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 14),
                        TextFormField(
                          controller: _notes,
                          maxLines: 4,
                          decoration: const InputDecoration(
                            labelText: 'Notes for the doctor',
                            alignLabelWithHint: true,
                          ),
                        ),
                        if (_error != null) ...[
                          const SizedBox(height: 12),
                          Text(
                            _error!,
                            style: TextStyle(
                              color: Theme.of(context).colorScheme.error,
                            ),
                          ),
                        ],
                        const SizedBox(height: 18),
                        FilledButton.icon(
                          onPressed: _busy ? null : _submit,
                          icon: _busy
                              ? const SizedBox(
                                  width: 18,
                                  height: 18,
                                  child: CircularProgressIndicator(
                                    strokeWidth: 2,
                                  ),
                                )
                              : const Icon(Icons.check),
                          label: const Text('Request appointment'),
                          style: FilledButton.styleFrom(
                            minimumSize: const Size.fromHeight(52),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}
