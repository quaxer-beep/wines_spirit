import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shared_core/shared_core.dart';

import 'src/providers/auth_provider.dart';
import 'src/providers/cart_provider.dart';
import 'src/providers/order_provider.dart';
import 'src/providers/product_provider.dart';
import 'src/screens/auth/login_screen.dart';
import 'src/screens/auth/register_screen.dart';
import 'src/screens/shop/home_screen.dart';
import 'src/screens/shop/products_screen.dart';
import 'src/screens/shop/product_detail_screen.dart';
import 'src/screens/cart/cart_screen.dart';
import 'src/screens/checkout/checkout_screen.dart';
import 'src/screens/orders/order_list_screen.dart';
import 'src/screens/orders/order_detail_screen.dart';
import 'src/screens/loyalty/loyalty_screen.dart';
import 'src/screens/verification/verification_screen.dart';
import 'src/screens/profile/profile_screen.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();

  final tokenStorage = TokenStorage();
  final apiClient = ApiClient(tokenStorage: tokenStorage);
  final authService = AuthService(api: apiClient, tokenStorage: tokenStorage);

  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(
          create: (_) => AuthProvider(authService: authService),
        ),
        ChangeNotifierProvider(
          create: (_) => ProductProvider(apiClient: apiClient),
        ),
        ChangeNotifierProvider(
          create: (_) => CartProvider(apiClient: apiClient),
        ),
        ChangeNotifierProvider(
          create: (_) => OrderProvider(apiClient: apiClient),
        ),
      ],
      child: const CustomerApp(),
    ),
  );
}

class CustomerApp extends StatelessWidget {
  const CustomerApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: AppConstants.customerAppName,
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      darkTheme: AppTheme.darkTheme,
      themeMode: ThemeMode.light,
      initialRoute: '/',
      onGenerateRoute: (settings) {
        switch (settings.name) {
          case '/':
            return MaterialPageRoute(
              builder: (_) => Consumer<AuthProvider>(
                builder: (context, auth, _) {
                  if (auth.isLoading) {
                    return const Scaffold(
                      body: Center(child: CircularProgressIndicator()),
                    );
                  }
                  if (auth.isAuthenticated) {
                    return const HomeScreen();
                  }
                  return const LoginScreen();
                },
              ),
            );
          case '/login':
            return MaterialPageRoute(
              builder: (_) => const LoginScreen(),
            );
          case '/register':
            return MaterialPageRoute(
              builder: (_) => const RegisterScreen(),
            );
          case '/products':
            return MaterialPageRoute(
              builder: (_) => const ProductsScreen(),
            );
          case '/cart':
            return MaterialPageRoute(
              builder: (_) => const CartScreen(),
            );
          case '/checkout':
            return MaterialPageRoute(
              builder: (_) => const CheckoutScreen(),
            );
          case '/orders':
            return MaterialPageRoute(
              builder: (_) => const OrderListScreen(),
            );
          case '/loyalty':
            return MaterialPageRoute(
              builder: (_) => const LoyaltyScreen(),
            );
          case '/verification':
            return MaterialPageRoute(
              builder: (_) => const VerificationScreen(),
            );
          case '/profile':
            return MaterialPageRoute(
              builder: (_) => const ProfileScreen(),
            );
          default:
            if (settings.name?.startsWith('/product/') == true) {
              final id = int.tryParse(settings.name!.split('/').last) ?? 0;
              return MaterialPageRoute(
                builder: (_) => ProductDetailScreen(productId: id),
              );
            }
            if (settings.name?.startsWith('/order/') == true) {
              final id = int.tryParse(settings.name!.split('/').last) ?? 0;
              return MaterialPageRoute(
                builder: (_) => OrderDetailScreen(orderId: id),
              );
            }
            return MaterialPageRoute(
              builder: (_) => const HomeScreen(),
            );
        }
      },
    );
  }
}
