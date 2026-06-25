import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shared_core/shared_core.dart';

import 'src/providers/exec_auth_provider.dart';
import 'src/providers/exec_dashboard_provider.dart';
import 'src/providers/analytics_provider.dart';
import 'src/providers/branch_provider.dart';
import 'src/providers/transfer_provider.dart';
import 'src/screens/auth/login_screen.dart';
import 'src/screens/dashboard/dashboard_screen.dart';
import 'src/screens/analytics/analytics_screen.dart';
import 'src/screens/analytics/kpi_detail_screen.dart';
import 'src/screens/analytics/comparison_screen.dart';
import 'src/screens/branches/branch_list_screen.dart';
import 'src/screens/branches/branch_detail_screen.dart';
import 'src/screens/transfers/transfer_list_screen.dart';
import 'src/screens/transfers/transfer_detail_screen.dart';

void main() {
  runApp(const ExecutiveApp());
}

class ExecutiveApp extends StatelessWidget {
  const ExecutiveApp({super.key});

  @override
  Widget build(BuildContext context) {
    final tokenStorage = TokenStorage();
    final apiClient = ApiClient(tokenStorage: tokenStorage);

    return MultiProvider(
      providers: [
        ChangeNotifierProvider(
          create: (_) => ExecAuthProvider(apiClient: apiClient)..checkAuth(),
        ),
        ChangeNotifierProvider(
          create: (_) => ExecDashboardProvider(apiClient: apiClient),
        ),
        ChangeNotifierProvider(
          create: (_) => AnalyticsProvider(apiClient: apiClient),
        ),
        ChangeNotifierProvider(
          create: (_) => BranchProvider(apiClient: apiClient),
        ),
        ChangeNotifierProvider(
          create: (_) => TransferProvider(apiClient: apiClient),
        ),
      ],
      child: MaterialApp(
        title: 'Executive BI',
        debugShowCheckedModeBanner: false,
        theme: ThemeData(
          useMaterial3: true,
          brightness: Brightness.light,
          primaryColor: AppColors.primary,
          scaffoldBackgroundColor: const Color(0xFFF5F0F1),
          colorScheme: const ColorScheme.light(
            primary: Color(0xFF7A1424),
            secondary: AppColors.loyaltyGold,
            surface: AppColors.surface,
            error: AppColors.error,
          ),
          appBarTheme: const AppBarTheme(
            backgroundColor: Color(0xFF7A1424),
            foregroundColor: Colors.white,
            elevation: 0,
            centerTitle: true,
          ),
          elevatedButtonTheme: ElevatedButtonThemeData(
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF7A1424),
              foregroundColor: Colors.white,
              minimumSize: const Size(double.infinity, 52),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
              ),
              textStyle: const TextStyle(
                fontFamily: 'Poppins',
                fontSize: 16,
                fontWeight: FontWeight.w600,
                letterSpacing: 0.5,
              ),
            ),
          ),
          cardTheme: CardTheme(
            elevation: 2,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
            ),
            margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
            color: AppColors.surface,
          ),
          inputDecorationTheme: InputDecorationTheme(
            filled: true,
            fillColor: const Color(0xFFF1EBEC),
            contentPadding: const EdgeInsets.symmetric(
              horizontal: 16,
              vertical: 16,
            ),
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide.none,
            ),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide.none,
            ),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: const BorderSide(
                color: Color(0xFF7A1424),
                width: 2,
              ),
            ),
            hintStyle: const TextStyle(
              fontFamily: 'Poppins',
              fontSize: 14,
              color: Color(0xFFADB5BD),
            ),
          ),
          dividerTheme: const DividerThemeData(
            color: Color(0xFFE9ECEF),
            thickness: 1,
          ),
          floatingActionButtonTheme: const FloatingActionButtonThemeData(
            backgroundColor: Color(0xFF7A1424),
            foregroundColor: Colors.white,
          ),
          textTheme: const TextTheme(
            displayLarge: AppTextStyles.displayLarge,
            displayMedium: AppTextStyles.displayMedium,
            displaySmall: AppTextStyles.displaySmall,
            headlineLarge: AppTextStyles.headlineLarge,
            headlineMedium: AppTextStyles.headlineMedium,
            headlineSmall: AppTextStyles.headlineSmall,
            titleLarge: AppTextStyles.titleLarge,
            titleMedium: AppTextStyles.titleMedium,
            bodyLarge: AppTextStyles.bodyLarge,
            bodyMedium: AppTextStyles.bodyMedium,
            bodySmall: AppTextStyles.bodySmall,
            labelLarge: AppTextStyles.labelLarge,
            labelMedium: AppTextStyles.labelMedium,
          ),
        ),
        initialRoute: '/',
        onGenerateRoute: (settings) {
          switch (settings.name) {
            case '/':
              return MaterialPageRoute(
                builder: (_) => const _AuthGate(),
              );
            case '/login':
              return MaterialPageRoute(
                builder: (_) => const LoginScreen(),
              );
            case '/dashboard':
              return MaterialPageRoute(
                builder: (_) => const DashboardScreen(),
              );
            case '/analytics':
              return MaterialPageRoute(
                builder: (_) => const AnalyticsScreen(),
              );
            case '/kpi-detail':
              return MaterialPageRoute(
                builder: (_) => const KpiDetailScreen(),
              );
            case '/branches':
              return MaterialPageRoute(
                builder: (_) => const BranchListScreen(),
              );
            case '/branch-detail':
              final branch = settings.arguments as Map<String, dynamic>;
              return MaterialPageRoute(
                builder: (_) => BranchDetailScreen(branch: branch),
              );
            case '/transfers':
              return MaterialPageRoute(
                builder: (_) => const TransferListScreen(),
              );
            case '/transfer-detail':
              final transfer = settings.arguments as Map<String, dynamic>;
              return MaterialPageRoute(
                builder: (_) => TransferDetailScreen(transfer: transfer),
              );
            case '/transfer-approve':
              final transfer = settings.arguments as Map<String, dynamic>;
              return MaterialPageRoute(
                builder: (_) => TransferDetailScreen(transfer: transfer),
              );
            default:
              return MaterialPageRoute(
                builder: (_) => const _AuthGate(),
              );
          }
        },
      ),
    );
  }
}

class _AuthGate extends StatelessWidget {
  const _AuthGate();

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<ExecAuthProvider>();

    if (auth.isLoading) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }

    if (auth.isLoggedIn) {
      return const DashboardScreen();
    }

    return const LoginScreen();
  }
}
