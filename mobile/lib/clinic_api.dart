import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

const _configuredApiUrl = String.fromEnvironment('API_BASE_URL');

String get apiBaseUrl {
  if (_configuredApiUrl.isNotEmpty) return _configuredApiUrl;
  return defaultTargetPlatform == TargetPlatform.android
      ? 'http://10.0.2.2:8000/api'
      : 'http://127.0.0.1:8000/api';
}

class ApiException implements Exception {
  const ApiException(this.message);
  final String message;

  @override
  String toString() => message;
}

class ClinicApi {
  ClinicApi({http.Client? client}) : _client = client ?? http.Client();

  final http.Client _client;
  String? token;

  Map<String, String> get _headers => {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    if (token != null) 'Authorization': 'Token $token',
  };

  Future<dynamic> _request(
    String path, {
    String method = 'GET',
    Map<String, dynamic>? body,
  }) async {
    final uri = Uri.parse('$apiBaseUrl/$path');
    late http.Response response;
    try {
      switch (method) {
        case 'POST':
          response = await _client.post(
            uri,
            headers: _headers,
            body: jsonEncode(body ?? {}),
          );
        default:
          response = await _client.get(uri, headers: _headers);
      }
    } catch (_) {
      throw ApiException('Could not reach the clinic server at $apiBaseUrl.');
    }
    final dynamic payload = response.body.isEmpty
        ? {}
        : jsonDecode(response.body);
    if (response.statusCode < 200 || response.statusCode >= 300) {
      if (payload is Map && payload['detail'] != null) {
        throw ApiException(payload['detail'].toString());
      }
      if (payload is Map) {
        final message = payload.values
            .expand((value) => value is List ? value : [value])
            .map((value) => value.toString())
            .join('\n');
        throw ApiException(message.isEmpty ? 'Request failed.' : message);
      }
      throw const ApiException('Request failed.');
    }
    return payload;
  }

  Future<Map<String, dynamic>> captchaChallenge() async =>
      await _request('auth/challenge/') as Map<String, dynamic>;

  Future<Map<String, dynamic>> login(
    String username,
    String password, {
    required String captchaChallenge,
    required String captchaAnswer,
  }) async {
    final result = await _request(
      'auth/login/',
      method: 'POST',
      body: {
        'username': username,
        'password': password,
        'captcha_challenge': captchaChallenge,
        'captcha_answer': captchaAnswer,
      },
    ) as Map<String, dynamic>;
    await _saveSession(result);
    return Map<String, dynamic>.from(result['user'] as Map);
  }

  Future<Map<String, dynamic>> register(Map<String, dynamic> values) async {
    final result = await _request(
      'auth/register/',
      method: 'POST',
      body: values,
    ) as Map<String, dynamic>;
    await _saveSession(result);
    return Map<String, dynamic>.from(result['user'] as Map);
  }

  Future<void> _saveSession(Map<String, dynamic> result) async {
    token = result['token'] as String;
    final preferences = await SharedPreferences.getInstance();
    await preferences.setString('clinic_token', token!);
    await preferences.setString('clinic_user', jsonEncode(result['user']));
  }

  Future<Map<String, dynamic>?> restoreSession() async {
    final preferences = await SharedPreferences.getInstance();
    token = preferences.getString('clinic_token');
    final savedUser = preferences.getString('clinic_user');
    if (token == null || savedUser == null) return null;
    try {
      final result = await _request('auth/me/') as Map<String, dynamic>;
      final user = Map<String, dynamic>.from(result['user'] as Map);
      await preferences.setString('clinic_user', jsonEncode(user));
      return user;
    } on ApiException {
      await signOut();
      return null;
    }
  }

  Future<void> signOut() async {
    token = null;
    final preferences = await SharedPreferences.getInstance();
    await preferences.remove('clinic_token');
    await preferences.remove('clinic_user');
  }

  Future<Map<String, dynamic>> dashboard() async =>
      await _request('mobile/dashboard/') as Map<String, dynamic>;

  Future<Map<String, dynamic>> adminOverview() async =>
      await _request('mobile/admin/') as Map<String, dynamic>;

  Future<List<Map<String, dynamic>>> doctors() async {
    final results = await _request('doctors/') as List<dynamic>;
    return results
        .map((item) => Map<String, dynamic>.from(item as Map))
        .toList();
  }

  Future<Map<String, dynamic>> bookAppointment(
    Map<String, dynamic> values,
  ) async {
    return await _request(
      'mobile/appointments/book/',
      method: 'POST',
      body: values,
    ) as Map<String, dynamic>;
  }

  Future<void> createDoctor(Map<String, dynamic> values) async {
    await _request('mobile/admin/doctors/', method: 'POST', body: values);
  }

  Future<void> decideAppointment(
    int id,
    String action, {
    String reason = '',
  }) async {
    await _request(
      'mobile/appointments/$id/decision/',
      method: 'POST',
      body: {'action': action, 'rejection_reason': reason},
    );
  }
}
