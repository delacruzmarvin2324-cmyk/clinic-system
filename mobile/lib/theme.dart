import 'package:flutter/material.dart';

class ClinicColors {
  static const navy = Color(0xFF1D2939);
  static const cyan = Color(0xFF08A9E8);
  static const mint = Color(0xFFF0FBF9);
  static const aqua = Color(0xFFDDF7F6);
  static const muted = Color(0xFF64748B);
  static const line = Color(0xFFDCE5EE);
  static const input = Color(0xFFF7F9FC);
  static const green = Color(0xFF159A82);
  static const red = Color(0xFFDF5458);
  static const amber = Color(0xFFC58222);

  static ThemeData build() {
    return ThemeData(
      useMaterial3: true,
      colorScheme: ColorScheme.fromSeed(
        seedColor: cyan,
        primary: cyan,
        secondary: green,
        surface: Colors.white,
        onSurface: navy,
      ),
      scaffoldBackgroundColor: mint,
      appBarTheme: const AppBarTheme(
        backgroundColor: Colors.white,
        foregroundColor: navy,
        elevation: 0,
        centerTitle: false,
        surfaceTintColor: Colors.white,
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: input,
        contentPadding: const EdgeInsets.symmetric(
          horizontal: 14,
          vertical: 13,
        ),
        hintStyle: const TextStyle(color: Color(0xFF98A4B3), fontSize: 14),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(9),
          borderSide: const BorderSide(color: line),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(9),
          borderSide: const BorderSide(color: line),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(9),
          borderSide: const BorderSide(color: cyan, width: 1.5),
        ),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          backgroundColor: cyan,
          foregroundColor: Colors.white,
          textStyle: const TextStyle(fontWeight: FontWeight.w700),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(9)),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: navy,
          side: const BorderSide(color: line),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(9)),
        ),
      ),
      textTheme: const TextTheme(
        headlineSmall: TextStyle(color: navy),
        titleLarge: TextStyle(color: navy),
        titleMedium: TextStyle(color: navy),
        bodyLarge: TextStyle(color: navy),
        bodyMedium: TextStyle(color: muted),
      ),
    );
  }
}
