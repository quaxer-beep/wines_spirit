import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shared_core/shared_core.dart';

import 'src/providers/manager_auth_provider.dart';
import 'src/providers/manager_dashboard_provider.dart';
import 'src/providers/inventory_provider.dart';
import 'src/providers/sales_provider.dart';
import 'src/providers/expense_provider.dart';
import 'src/providers/approval_provider.dart';
import 'src/providers/staff_provider.dart';
import 'src/screens/auth/login_screen.dart';
import 'src/screens/dashboard/dashboard_screen.dart';
import 'src/screens/inventory/inventory_screen.dart';
import 'src/screens/inventory/stock_detail_screen.dart';
import 'src/screens/sales/sales_screen.dart';
import 'src/screens/expenses/expense_list_screen.dart';
import 'src/screens/expenses/expense_form_screen.dart';
import 'src/screens/approvals/approval_list_screen.dart';
import 'src/screens/approvals/approval_detail_screen.dart';
import 'src/screens/staff/staff_list_screen.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  final tokenStorage = TokenStorage();
  final apiClient = ApiClient(tokenStorage: tokenStorage);
  runApp(ManagerApp(apiClient: apiClient, tokenStorage: tokenStorage));
}

class ManagerApp extends StatelessWidget {
  final ApiClient apiClient;
  final TokenStorage tokenStorage;

  const ManagerApp({
    super.key,
    required this.apiClient,
    required this.tokenStorage,
  });

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(
          create: (_) => ManagerAuthProvider(api: apiClient, tokenStorage: tokenStorage),
        ),
        ChangeNotifierProvider(
          create: (_) => ManagerDashboardProvider(api: apiClient),
        ),
        ChangeNotifierProvider(
          create: (_) => InventoryProvider(api: apiClient),
        ),
        ChangeNotifierProvider(
          create: (_) => SalesProvider(api: apiClient),
        ),
        ChangeNotifierProvider(
          create: (_) => ExpenseProvider(api: apiClient),
        ),
        ChangeNotifierProvider(
          create: (_) => ApprovalProvider(api: apiClient),
        ),
        ChangeNotifierProvider(
          create: (_) => StaffProvider(api: apiClient),
        ),
      ],
      child: MaterialApp(
        title: AppConstants.managerAppName,
        debugShowCheckedModeBanner: false,
        theme: AppTheme.lightTheme,
        home: const AuthGate(),
        routes: {
          '/login': (_) => const LoginScreen(),
          '/dashboard': (_) => const DashboardScreen(),
          '/inventory': (_) => const InventoryScreen(),
          '/inventory-detail': (ctx) {
            final item = ModalRoute.of(ctx)?.settings.arguments as Map<String, dynamic>?;
            return StockDetailScreen(item: item);
          },
          '/sales': (_) => const SalesScreen(),
          '/expenses': (_) => const ExpenseListScreen(),
          '/expense-add': (_) => const ExpenseFormScreen(),
          '/approvals': (_) => const ApprovalListScreen(),
          '/approval-detail': (ctx) {
            final approval = ModalRoute.of(ctx)?.settings.arguments as Map<String, dynamic>?;
            return ApprovalDetailScreen(approval: approval);
          },
          '/staff': (_) => const StaffListScreen(),
          '/staff-detail': (ctx) {
            final staff = ModalRoute.of(ctx)?.settings.arguments as Map<String, dynamic>?;
            return _PlaceholderScreen(
              title: staff?['full_name'] as String? ?? staff?['name'] as String? ?? 'Staff Detail',
            );
          },
          '/profile': (ctx) => const _PlaceholderScreen(title: 'Profile'),
        },
      ),
    );
  }
}

class AuthGate extends StatefulWidget {
  const AuthGate({super.key});

  @override
  State<AuthGate> createState() => _AuthGateState();
}

class _AuthGateState extends State<AuthGate> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<ManagerAuthProvider>().checkAuth();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<ManagerAuthProvider>(
      builder: (context, auth, _) {
        if (auth.isLoading) {
          return const Scaffold(
            body: Center(child: CircularProgressIndicator()),
          );
        }
        if (auth.isLoggedIn) {
          return const DashboardScreen();
        }
        return const LoginScreen();
      },
    );
  }
}

class _PlaceholderScreen extends StatelessWidget {
  final String title;

  const _PlaceholderScreen({required this.title});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(title)),
      body: const Center(
        child: Text('Coming soon', style: AppTextStyles.bodyMedium),
      ),
    );
  }
}
