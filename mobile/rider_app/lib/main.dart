import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shared_core/shared_core.dart';

import 'src/providers/rider_auth_provider.dart';
import 'src/providers/rider_delivery_provider.dart';
import 'src/providers/rider_incident_provider.dart';
import 'src/providers/rider_location_provider.dart';
import 'src/screens/auth/login_screen.dart';
import 'src/screens/deliveries/delivery_list_screen.dart';
import 'src/screens/deliveries/delivery_detail_screen.dart';
import 'src/screens/deliveries/age_verification_screen.dart';
import 'src/screens/deliveries/payment_screen.dart';
import 'src/screens/incidents/incident_report_screen.dart';
import 'src/screens/incidents/incident_list_screen.dart';
import 'src/screens/navigation/navigation_screen.dart';
import 'src/screens/profile/rider_profile_screen.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();

  final tokenStorage = TokenStorage();
  final apiClient = ApiClient(tokenStorage: tokenStorage);

  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(
          create: (_) => RiderAuthProvider(
            apiClient: apiClient,
            tokenStorage: tokenStorage,
          ),
        ),
        ChangeNotifierProvider(
          create: (_) => RiderDeliveryProvider(apiClient: apiClient),
        ),
        ChangeNotifierProvider(
          create: (_) => RiderIncidentProvider(apiClient: apiClient),
        ),
        ChangeNotifierProvider(
          create: (_) => RiderLocationProvider(apiClient: apiClient),
        ),
      ],
      child: const RiderApp(),
    ),
  );
}

class RiderApp extends StatelessWidget {
  const RiderApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: AppConstants.riderAppName,
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      darkTheme: AppTheme.darkTheme,
      themeMode: ThemeMode.light,
      initialRoute: '/',
      onGenerateRoute: (settings) {
        switch (settings.name) {
          case '/':
            return MaterialPageRoute(
              builder: (_) => Consumer<RiderAuthProvider>(
                builder: (context, auth, _) {
                  if (auth.isLoading) {
                    return const Scaffold(
                      body: Center(child: CircularProgressIndicator()),
                    );
                  }
                  if (auth.isLoggedIn) {
                    return const DeliveryListScreen();
                  }
                  return const RiderLoginScreen();
                },
              ),
            );
          case '/login':
            return MaterialPageRoute(
              builder: (_) => const RiderLoginScreen(),
            );
          case '/deliveries':
            return MaterialPageRoute(
              builder: (_) => const DeliveryListScreen(),
            );
          case '/delivery-detail':
            final delivery = settings.arguments as RiderDelivery;
            return MaterialPageRoute(
              builder: (_) => DeliveryDetailScreen(delivery: delivery),
            );
          case '/age-verification':
            final args = settings.arguments as Map<String, dynamic>;
            return MaterialPageRoute(
              builder: (_) => AgeVerificationScreen(
                delivery: args['delivery'] as RiderDelivery,
              ),
            );
          case '/payment':
            final args = settings.arguments as Map<String, dynamic>;
            return MaterialPageRoute(
              builder: (_) => PaymentScreen(
                delivery: args['delivery'] as RiderDelivery,
              ),
            );
          case '/incident-report':
            final delivery = settings.arguments as RiderDelivery?;
            return MaterialPageRoute(
              builder: (_) => IncidentReportScreen(
                deliveryId: delivery?.id,
              ),
            );
          case '/incident-list':
            return MaterialPageRoute(
              builder: (_) => const IncidentListScreen(),
            );
          case '/navigation':
            final delivery = settings.arguments as RiderDelivery;
            return MaterialPageRoute(
              builder: (_) => NavigationScreen(delivery: delivery),
            );
          case '/profile':
            return MaterialPageRoute(
              builder: (_) => const RiderProfileScreen(),
            );
          default:
            return MaterialPageRoute(
              builder: (_) => const RiderLoginScreen(),
            );
        }
      },
    );
  }
}
