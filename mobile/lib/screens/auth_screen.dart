import 'package:flutter/material.dart';

import '../clinic_api.dart';
import '../theme.dart';
import '../widgets/brand_logo.dart';

class AuthScreen extends StatefulWidget {
  const AuthScreen({
    super.key,
    required this.api,
    required this.onAuthenticated,
  });

  final ClinicApi api;
  final ValueChanged<Map<String, dynamic>> onAuthenticated;

  @override
  State<AuthScreen> createState() => _AuthScreenState();
}

class _AuthScreenState extends State<AuthScreen> {
  final _formKey = GlobalKey<FormState>();
  final _username = TextEditingController();
  final _password = TextEditingController();
  final _firstName = TextEditingController();
  final _lastName = TextEditingController();
  final _email = TextEditingController();
  final _phone = TextEditingController();
  final _confirmPassword = TextEditingController();
  final _captchaAnswer = TextEditingController();
  DateTime? _birthDate;
  Map<String, dynamic>? _captcha;
  bool _captchaLoading = false;
  String? _captchaError;
  bool _registering = false;
  bool _busy = false;
  bool _obscurePassword = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _refreshCaptcha();
  }

  @override
  void dispose() {
    _username.dispose();
    _password.dispose();
    _firstName.dispose();
    _lastName.dispose();
    _email.dispose();
    _phone.dispose();
    _confirmPassword.dispose();
    _captchaAnswer.dispose();
    super.dispose();
  }

  Future<void> _refreshCaptcha() async {
    setState(() {
      _captchaLoading = true;
      _captchaError = null;
    });
    try {
      final captcha = await widget.api.captchaChallenge();
      if (mounted) setState(() => _captcha = captcha);
    } on ApiException catch (error) {
      if (mounted) setState(() => _captchaError = error.message);
    } finally {
      if (mounted) setState(() => _captchaLoading = false);
    }
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    if (_registering && _birthDate == null) {
      setState(() => _error = 'Choose your date of birth.');
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final user = _registering
          ? await widget.api.register({
              'username': _username.text.trim(),
              'password': _password.text,
              'first_name': _firstName.text.trim(),
              'last_name': _lastName.text.trim(),
              'email': _email.text.trim(),
              'phone_number': _phone.text.trim(),
              'date_of_birth': _birthDate!.toIso8601String().substring(0, 10),
            })
          : await widget.api.login(
              _username.text.trim(),
              _password.text,
              captchaChallenge: _captcha?['challenge'] as String? ?? '',
              captchaAnswer: _captchaAnswer.text.trim(),
            );
      if (mounted) widget.onAuthenticated(user);
    } on ApiException catch (error) {
      if (mounted) {
        setState(() {
          _error = error.message;
          _captchaAnswer.clear();
        });
        if (!_registering) _refreshCaptcha();
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _chooseBirthDate() async {
    final now = DateTime.now();
    final selected = await showDatePicker(
      context: context,
      initialDate: DateTime(now.year - 25),
      firstDate: DateTime(1900),
      lastDate: now,
    );
    if (selected != null) setState(() => _birthDate = selected);
  }

  Widget _field(
    String label,
    TextEditingController controller, {
    TextInputType? keyboardType,
    bool obscure = false,
    TextCapitalization textCapitalization = TextCapitalization.none,
    String? Function(String?)? validator,
  }) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 13),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.only(left: 2, bottom: 6),
            child: Text(
              label,
              style: const TextStyle(
                color: ClinicColors.navy,
                fontSize: 12,
                fontWeight: FontWeight.w700,
              ),
            ),
          ),
          TextFormField(
            controller: controller,
            keyboardType: keyboardType,
            textCapitalization: textCapitalization,
            obscureText: obscure,
            validator:
                validator ??
                (value) =>
                    (value == null || value.trim().isEmpty) ? 'Required' : null,
            decoration: InputDecoration(
              hintText: 'Enter ${label.toLowerCase()}',
              isDense: true,
            ),
          ),
        ],
      ),
    );
  }

  Widget _passwordField() {
    return Padding(
      padding: const EdgeInsets.only(bottom: 13),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Padding(
            padding: EdgeInsets.only(left: 2, bottom: 6),
            child: Text(
              'Password',
              style: TextStyle(
                color: ClinicColors.navy,
                fontSize: 12,
                fontWeight: FontWeight.w700,
              ),
            ),
          ),
          TextFormField(
            controller: _password,
            obscureText: _obscurePassword,
            validator: (value) => value != null && value.length >= 8
                ? null
                : 'Use at least 8 characters',
            decoration: InputDecoration(
              hintText: 'Enter password',
              isDense: true,
              suffixIcon: IconButton(
                tooltip: _obscurePassword ? 'Show password' : 'Hide password',
                onPressed: () =>
                    setState(() => _obscurePassword = !_obscurePassword),
                icon: Icon(
                  _obscurePassword
                      ? Icons.visibility_outlined
                      : Icons.visibility_off_outlined,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    final compact = MediaQuery.sizeOf(context).width < 460;
    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            Container(
              height: 60,
              padding: const EdgeInsets.symmetric(horizontal: 20),
              color: Colors.white,
              child: Row(
                children: [
                  const BrandLogo(compact: true),
                  const Spacer(),
                  TextButton(
                    onPressed: () => setState(() => _registering = false),
                    child: const Text('Login'),
                  ),
                  const SizedBox(width: 6),
                  FilledButton(
                    onPressed: () => setState(() => _registering = true),
                    style: FilledButton.styleFrom(
                      minimumSize: Size(compact ? 78 : 132, 38),
                      padding: const EdgeInsets.symmetric(horizontal: 12),
                    ),
                    child: Text(compact ? 'Register' : 'Register Patient'),
                  ),
                ],
              ),
            ),
            Expanded(
              child: Container(
                width: double.infinity,
                color: ClinicColors.mint,
                alignment: Alignment.center,
                child: SingleChildScrollView(
                  padding: const EdgeInsets.all(20),
                  child: ConstrainedBox(
                    constraints: BoxConstraints(
                      maxWidth: _registering ? 420 : 370,
                    ),
                    child: Container(
                      padding: EdgeInsets.all(_registering ? 26 : 30),
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(14),
                        border: Border.all(color: ClinicColors.line),
                        boxShadow: const [
                          BoxShadow(
                            color: Color(0x120F3550),
                            blurRadius: 24,
                            offset: Offset(0, 8),
                          ),
                        ],
                      ),
                      child: Form(
                        key: _formKey,
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                            Text(
                              _registering
                                  ? 'Create Patient Account'
                                  : 'Welcome Back',
                              textAlign: TextAlign.center,
                              style: const TextStyle(
                                color: ClinicColors.navy,
                                fontSize: 25,
                                fontWeight: FontWeight.w800,
                              ),
                            ),
                            const SizedBox(height: 5),
                            Text(
                              _registering
                                  ? 'Join us to book your consultations'
                                  : 'Enter your credentials to access your account',
                              textAlign: TextAlign.center,
                              style: const TextStyle(
                                color: ClinicColors.muted,
                                fontSize: 13,
                              ),
                            ),
                            const SizedBox(height: 24),
                            _field(
                              'Username',
                              _username,
                              textCapitalization: TextCapitalization.none,
                            ),
                            if (_registering) ...[
                              _field('First name', _firstName),
                              _field('Last name', _lastName),
                              _field(
                                'Email',
                                _email,
                                keyboardType: TextInputType.emailAddress,
                                validator: (value) =>
                                    value != null && value.contains('@')
                                    ? null
                                    : 'Enter a valid email',
                              ),
                            ],
                            _passwordField(),
                            if (_registering) ...[
                              _field(
                                'Confirm password',
                                _confirmPassword,
                                obscure: true,
                                validator: (value) => value == _password.text
                                    ? null
                                    : 'Passwords do not match',
                              ),
                              _field(
                                'Phone number',
                                _phone,
                                keyboardType: TextInputType.phone,
                              ),
                              OutlinedButton.icon(
                                onPressed: _chooseBirthDate,
                                icon: const Icon(Icons.calendar_month_outlined),
                                label: Text(
                                  _birthDate == null
                                      ? 'Date of birth'
                                      : '${_birthDate!.year}-${_birthDate!.month.toString().padLeft(2, '0')}-${_birthDate!.day.toString().padLeft(2, '0')}',
                                ),
                                style: OutlinedButton.styleFrom(
                                  minimumSize: const Size.fromHeight(46),
                                  alignment: Alignment.centerLeft,
                                ),
                              ),
                              const SizedBox(height: 14),
                            ],
                            if (!_registering) ...[
                              Row(
                                children: [
                                  Expanded(
                                    child: Text(
                                      _captcha?['question']?.toString() ??
                                          (_captchaLoading
                                              ? 'Loading math challenge...'
                                              : 'Challenge unavailable. Tap refresh.'),
                                      style: const TextStyle(
                                        color: ClinicColors.navy,
                                        fontSize: 12,
                                        fontWeight: FontWeight.w700,
                                      ),
                                    ),
                                  ),
                                  IconButton(
                                    tooltip: 'Refresh math challenge',
                                    onPressed: _captchaLoading
                                        ? null
                                        : _refreshCaptcha,
                                    icon: _captchaLoading
                                        ? const SizedBox.square(
                                            dimension: 18,
                                            child: CircularProgressIndicator(
                                              strokeWidth: 2,
                                            ),
                                          )
                                        : const Icon(Icons.refresh),
                                    visualDensity: VisualDensity.compact,
                                  ),
                                ],
                              ),
                              if (_captchaError != null) ...[
                                Text(
                                  _captchaError!,
                                  style: TextStyle(color: colors.error),
                                ),
                                const SizedBox(height: 10),
                              ],
                              _field(
                                'Your answer',
                                _captchaAnswer,
                                keyboardType: TextInputType.number,
                              ),
                              const Padding(
                                padding: EdgeInsets.only(top: 0, bottom: 12),
                                child: Text(
                                  "Please solve this math problem to prove you're human.",
                                  style: TextStyle(
                                    color: ClinicColors.muted,
                                    fontSize: 11,
                                  ),
                                ),
                              ),
                            ],
                            if (_error != null) ...[
                              Text(
                                _error!,
                                style: TextStyle(color: colors.error),
                              ),
                              const SizedBox(height: 10),
                            ],
                            FilledButton(
                              onPressed: _busy ? null : _submit,
                              style: FilledButton.styleFrom(
                                minimumSize: const Size.fromHeight(46),
                              ),
                              child: _busy
                                  ? const SizedBox(
                                      width: 20,
                                      height: 20,
                                      child: CircularProgressIndicator(
                                        strokeWidth: 2,
                                      ),
                                    )
                                  : Text(
                                      _registering
                                          ? 'Register Account'
                                          : 'Login  →',
                                    ),
                            ),
                            const SizedBox(height: 8),
                            Center(
                              child: TextButton(
                                onPressed: _busy
                                    ? null
                                    : () => setState(() {
                                        _registering = !_registering;
                                        _error = null;
                                        _captchaAnswer.clear();
                                      }),
                                child: Text(
                                  _registering
                                      ? 'Already have an account? Login here'
                                      : 'New patient? Register here',
                                  style: const TextStyle(fontSize: 12),
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
