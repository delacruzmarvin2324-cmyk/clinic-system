import 'package:flutter/material.dart';

import '../theme.dart';

class BrandLogo extends StatelessWidget {
  const BrandLogo({super.key, this.compact = false});

  final bool compact;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(
          Icons.monitor_heart_rounded,
          size: compact ? 25 : 29,
          color: ClinicColors.navy,
        ),
        const SizedBox(width: 8),
        Text.rich(
          TextSpan(
            children: [
              const TextSpan(text: 'Medi'),
              TextSpan(
                text: ' Care',
                style: TextStyle(color: ClinicColors.cyan),
              ),
            ],
          ),
          style: TextStyle(
            color: ClinicColors.navy,
            fontSize: compact ? 18 : 21,
            fontWeight: FontWeight.w800,
          ),
        ),
      ],
    );
  }
}
