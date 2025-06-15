import logging
import time
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from binance import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException
from dotenv import load_dotenv
import argparse
import sys

class TradingBot:
    """
    A comprehensive trading bot for Binance Futures Testnet
    Supports market, limit, and stop-limit orders with proper logging and error handling
    """
    
    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        """
        Initialize the trading bot
        
        Args:
            api_key (str): Binance API key
            api_secret (str): Binance API secret
            testnet (bool): Whether to use testnet (default: True)
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        
        # Initialize Binance client
        self.client = Client(
            api_key=api_key,
            api_secret=api_secret,
            testnet=testnet
        )
        
        # Set up logging
        self.setup_logging()
        
        # Test connection
        self.test_connection()
        
    def setup_logging(self):
        """Set up logging configuration"""
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.FileHandler(f'trading_bot_{datetime.now().strftime("%Y%m%d")}.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def test_connection(self):
        """Test API connection and log the result"""
        try:
            account_info = self.client.futures_account()
            self.logger.info("Successfully connected to Binance Futures Testnet")
            self.logger.info(f"Account Balance: {account_info.get('totalWalletBalance', 'N/A')} USDT")
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to Binance API: {str(e)}")
            return False
    
    def get_account_info(self) -> Dict[str, Any]:
        """Get account information"""
        try:
            account_info = self.client.futures_account()
            self.logger.info("Account information retrieved successfully")
            return account_info
        except BinanceAPIException as e:
            self.logger.error(f"API Error getting account info: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error getting account info: {e}")
            raise
    
    def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """Get symbol information and validate if trading is allowed"""
        try:
            exchange_info = self.client.futures_exchange_info()
            symbol_info = None
            
            for s in exchange_info['symbols']:
                if s['symbol'] == symbol.upper():
                    symbol_info = s
                    break
            
            if not symbol_info:
                raise ValueError(f"Symbol {symbol} not found")
            
            if symbol_info['status'] != 'TRADING':
                raise ValueError(f"Symbol {symbol} is not available for trading")
            
            self.logger.info(f"Symbol {symbol} is valid and available for trading")
            return symbol_info
            
        except BinanceAPIException as e:
            self.logger.error(f"API Error getting symbol info: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error validating symbol: {e}")
            raise
    
    def get_current_price(self, symbol: str) -> float:
        """Get current price for a symbol"""
        try:
            ticker = self.client.futures_symbol_ticker(symbol=symbol.upper())
            price = float(ticker['price'])
            self.logger.info(f"Current price for {symbol}: {price}")
            return price
        except Exception as e:
            self.logger.error(f"Error getting current price for {symbol}: {e}")
            raise
    
    def place_market_order(self, symbol: str, side: str, quantity: float) -> Dict[str, Any]:
        """
        Place a market order
        
        Args:
            symbol (str): Trading symbol (e.g., 'BTCUSDT')
            side (str): 'BUY' or 'SELL'
            quantity (float): Quantity to trade
            
        Returns:
            Dict: Order response
        """
        try:
            self.logger.info(f"Placing MARKET {side} order: {quantity} {symbol}")
            
            order = self.client.futures_create_order(
                symbol=symbol.upper(),
                side=side.upper(),
                type=Client.ORDER_TYPE_MARKET,
                quantity=quantity
            )
            
            self.logger.info(f"Market order placed successfully!")
            self.logger.info(f"Order ID: {order['orderId']}")
            self.logger.info(f"Status: {order['status']}")
            
            return order
            
        except BinanceOrderException as e:
            self.logger.error(f"Order Error: {e}")
            raise
        except BinanceAPIException as e:
            self.logger.error(f"API Error: {e}")
            raise
        except Exception as e:
            self.logger.error(f" Unexpected error placing market order: {e}")
            raise
    
    def place_limit_order(self, symbol: str, side: str, quantity: float, price: float) -> Dict[str, Any]:
        """
        Place a limit order
        
        Args:
            symbol (str): Trading symbol (e.g., 'BTCUSDT')
            side (str): 'BUY' or 'SELL'
            quantity (float): Quantity to trade
            price (float): Limit price
            
        Returns:
            Dict: Order response
        """
        try:
            self.logger.info(f"Placing LIMIT {side} order: {quantity} {symbol} at {price}")
            
            order = self.client.futures_create_order(
                symbol=symbol.upper(),
                side=side.upper(),
                type=Client.ORDER_TYPE_LIMIT,
                quantity=quantity,
                price=price,
                timeInForce=Client.TIME_IN_FORCE_GTC
            )
            
            self.logger.info(f"Limit order placed successfully!")
            self.logger.info(f"Order ID: {order['orderId']}")
            self.logger.info(f"Status: {order['status']}")
            
            return order
            
        except BinanceOrderException as e:
            self.logger.error(f"Order Error: {e}")
            raise
        except BinanceAPIException as e:
            self.logger.error(f"API Error: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error placing limit order: {e}")
            raise
    
    def place_stop_limit_order(self, symbol: str, side: str, quantity: float, 
                              stop_price: float, limit_price: float) -> Dict[str, Any]:
        """
        Place a stop-limit order (Bonus feature)
        
        Args:
            symbol (str): Trading symbol
            side (str): 'BUY' or 'SELL'
            quantity (float): Quantity to trade
            stop_price (float): Stop price to trigger the order
            limit_price (float): Limit price for the order
            
        Returns:
            Dict: Order response
        """
        try:
            self.logger.info(f"Placing STOP_LIMIT {side} order: {quantity} {symbol}")
            self.logger.info(f"Stop Price: {stop_price}, Limit Price: {limit_price}")
            
            order = self.client.futures_create_order(
                symbol=symbol.upper(),
                side=side.upper(),
                type='STOP',
                quantity=quantity,
                stopPrice=stop_price,
                price=limit_price,
                timeInForce='GTC'
            )
            
            self.logger.info(f"Stop-limit order placed successfully!")
            self.logger.info(f"Order ID: {order['orderId']}")
            self.logger.info(f"Status: {order['status']}")
            
            return order
            
        except BinanceOrderException as e:
            self.logger.error(f"Order Error: {e}")
            raise
        except BinanceAPIException as e:
            self.logger.error(f"API Error: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error placing stop-limit order: {e}")
            raise
    
    def get_order_status(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """Get order status"""
        try:
            order = self.client.futures_get_order(symbol=symbol.upper(), orderId=order_id)
            self.logger.info(f"Order {order_id} status: {order['status']}")
            return order
        except Exception as e:
            self.logger.error(f"Error getting order status: {e}")
            raise
    
    def cancel_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """Cancel an order"""
        try:
            result = self.client.futures_cancel_order(symbol=symbol.upper(), orderId=order_id)
            self.logger.info(f"Order {order_id} cancelled successfully")
            return result
        except Exception as e:
            self.logger.error(f"Error cancelling order {order_id}: {e}")
            raise
    
    def get_open_orders(self, symbol: str = None) -> List[Dict[str, Any]]:
        """Get all open orders"""
        try:
            if symbol:
                orders = self.client.futures_get_open_orders(symbol=symbol.upper())
            else:
                orders = self.client.futures_get_open_orders()
            
            self.logger.info(f"📋 Found {len(orders)} open orders")
            return orders
        except Exception as e:
            self.logger.error(f"Error getting open orders: {e}")
            raise
    
    def display_order_details(self, order: Dict[str, Any]):
        """Display order details in a formatted way"""
        print("\n" + "="*50)
        print("ORDER DETAILS")
        print("="*50)
        print(f"Order ID: {order.get('orderId', 'N/A')}")
        print(f"Symbol: {order.get('symbol', 'N/A')}")
        print(f"Side: {order.get('side', 'N/A')}")
        print(f"Type: {order.get('type', 'N/A')}")
        print(f"Quantity: {order.get('origQty', 'N/A')}")
        print(f"Price: {order.get('price', 'N/A')}")
        print(f"Status: {order.get('status', 'N/A')}")
        print(f"Time: {datetime.fromtimestamp(order.get('time', 0)/1000)}")
        if 'stopPrice' in order and order['stopPrice'] != '0':
            print(f"Stop Price: {order['stopPrice']}")
        print("="*50)


class TradingBotCLI:
    """Command Line Interface for the Trading Bot"""
    
    def __init__(self):
        self.bot = None
        
    def setup_bot(self):
        """Setup the trading bot with API credentials"""
        print("Binance Futures Trading Bot Setup")
        print("=====================================")
        
        # Get API credentials
        api_key = input("Enter your Binance API Key: ").strip()
        api_secret = input("Enter your Binance API Secret: ").strip()
        
        if not api_key or not api_secret:
            print("API credentials are required!")
            return False
        
        try:
            self.bot = TradingBot(api_key, api_secret, testnet=True)
            return True
        except Exception as e:
            print(f"Failed to initialize bot: {e}")
            return False
    
    def validate_inputs(self, symbol: str, side: str, quantity: str) -> tuple:
        """Validate common inputs"""
        # Validate symbol
        if not symbol:
            raise ValueError("Symbol is required")
        
        # Validate side
        if side.upper() not in ['BUY', 'SELL']:
            raise ValueError("Side must be 'BUY' or 'SELL'")
        
        # Validate quantity
        try:
            qty = float(quantity)
            if qty <= 0:
                raise ValueError("Quantity must be positive")
        except ValueError:
            raise ValueError("Invalid quantity format")
        
        return symbol.upper(), side.upper(), qty
    
    def market_order_menu(self):
        """Handle market order placement"""
        print("\nMARKET ORDER")
        print("================")
        
        try:
            symbol = input("Enter symbol (e.g., BTCUSDT): ").strip()
            side = input("Enter side (BUY/SELL): ").strip()
            quantity = input("Enter quantity: ").strip()
            
            symbol, side, qty = self.validate_inputs(symbol, side, quantity)
            
            # Get current price for reference
            current_price = self.bot.get_current_price(symbol)
            print(f"Current price: {current_price}")
            
            confirm = input(f"Confirm {side} {qty} {symbol} at market price? (y/N): ").strip().lower()
            
            if confirm == 'y':
                order = self.bot.place_market_order(symbol, side, qty)
                self.bot.display_order_details(order)
            else:
                print("Order cancelled.")
                
        except Exception as e:
            print(f"Error: {e}")
    
    def limit_order_menu(self):
        """Handle limit order placement"""
        print("\n📊 LIMIT ORDER")
        print("===============")
        
        try:
            symbol = input("Enter symbol (e.g., BTCUSDT): ").strip()
            side = input("Enter side (BUY/SELL): ").strip()
            quantity = input("Enter quantity: ").strip()
            price = input("Enter limit price: ").strip()
            
            symbol, side, qty = self.validate_inputs(symbol, side, quantity)
            
            try:
                limit_price = float(price)
                if limit_price <= 0:
                    raise ValueError("Price must be positive")
            except ValueError:
                raise ValueError("Invalid price format")
            
            # Get current price for reference
            current_price = self.bot.get_current_price(symbol)
            print(f"Current price: {current_price}")
            
            confirm = input(f"Confirm {side} {qty} {symbol} at {limit_price}? (y/N): ").strip().lower()
            
            if confirm == 'y':
                order = self.bot.place_limit_order(symbol, side, qty, limit_price)
                self.bot.display_order_details(order)
            else:
                print("Order cancelled.")
                
        except Exception as e:
            print(f"Error: {e}")
    
    def stop_limit_order_menu(self):
        """Handle stop-limit order placement"""
        print("\nSTOP-LIMIT ORDER")
        print("===================")
        
        try:
            symbol = input("Enter symbol (e.g., BTCUSDT): ").strip()
            side = input("Enter side (BUY/SELL): ").strip()
            quantity = input("Enter quantity: ").strip()
            stop_price = input("Enter stop price: ").strip()
            limit_price = input("Enter limit price: ").strip()
            
            symbol, side, qty = self.validate_inputs(symbol, side, quantity)
            
            try:
                stop_px = float(stop_price)
                limit_px = float(limit_price)
                if stop_px <= 0 or limit_px <= 0:
                    raise ValueError("Prices must be positive")
            except ValueError:
                raise ValueError("Invalid price format")
            
            # Get current price for reference
            current_price = self.bot.get_current_price(symbol)
            print(f"Current price: {current_price}")
            
            confirm = input(f"Confirm {side} {qty} {symbol} (Stop: {stop_px}, Limit: {limit_px})? (y/N): ").strip().lower()
            
            if confirm == 'y':
                order = self.bot.place_stop_limit_order(symbol, side, qty, stop_px, limit_px)
                self.bot.display_order_details(order)
            else:
                print("Order cancelled.")
                
        except Exception as e:
            print(f"Error: {e}")
    
    def view_account_menu(self):
        """Display account information"""
        try:
            account_info = self.bot.get_account_info()
            
            print("\n💰 ACCOUNT INFORMATION")
            print("======================")
            print(f"Total Wallet Balance: {account_info.get('totalWalletBalance', 'N/A')} USDT")
            print(f"Available Balance: {account_info.get('availableBalance', 'N/A')} USDT")
            print(f"Total Unrealized PnL: {account_info.get('totalUnrealizedProfit', 'N/A')} USDT")
            
            # Show positions if any
            positions = [pos for pos in account_info.get('positions', []) if float(pos['positionAmt']) != 0]
            if positions:
                print(f"\nOpen Positions: {len(positions)}")
                for pos in positions:
                    print(f"  {pos['symbol']}: {pos['positionAmt']} (PnL: {pos['unrealizedProfit']} USDT)")
            
        except Exception as e:
            print(f"Error getting account info: {e}")
    
    def view_orders_menu(self):
        """Display open orders"""
        try:
            orders = self.bot.get_open_orders()
            
            if not orders:
                print("\nNo open orders found.")
                return
            
            print(f"\nOPEN ORDERS ({len(orders)})")
            print("="*60)
            
            for order in orders:
                print(f"ID: {order['orderId']} | {order['symbol']} | {order['side']} | {order['type']}")
                print(f"Qty: {order['origQty']} | Price: {order['price']} | Status: {order['status']}")
                print("-" * 60)
                
        except Exception as e:
            print(f"Error getting orders: {e}")
    
    def main_menu(self):
        """Main menu loop"""
        if not self.setup_bot():
            return
        
        while True:
            print("\nBINANCE FUTURES TRADING BOT")
            print("===============================")
            print("1. Place Market Order")
            print("2. Place Limit Order")
            print("3. Place Stop-Limit Order")
            print("4. View Account Info")
            print("5. View Open Orders")
            print("6. Exit")
            print("===============================")
            
            choice = input("Select an option (1-6): ").strip()
            
            if choice == '1':
                self.market_order_menu()
            elif choice == '2':
                self.limit_order_menu()
            elif choice == '3':
                self.stop_limit_order_menu()
            elif choice == '4':
                self.view_account_menu()
            elif choice == '5':
                self.view_orders_menu()
            elif choice == '6':
                print("Goodbye!")
                break
            else:
                print("Invalid option. Please try again.")


def main():
    """Main function to run the trading bot"""
    load_dotenv()
    parser = argparse.ArgumentParser(description='Binance Futures Trading Bot')
    parser.add_argument('--symbol', help='Trading symbol (e.g., BTCUSDT)')
    parser.add_argument('--side', choices=['BUY', 'SELL'], help='Order side')
    parser.add_argument('--type', choices=['MARKET', 'LIMIT', 'STOP_LIMIT'], help='Order type')
    parser.add_argument('--quantity', type=float, help='Order quantity')
    parser.add_argument('--price', type=float, help='Limit price')
    parser.add_argument('--stop-price', type=float, help='Stop price for stop-limit orders')
    
    args = parser.parse_args()
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")
    
    # If command line arguments are provided, use them
    if all([api_key, api_secret, args.symbol, args.side, args.type, args.quantity]):
        try:
            bot = TradingBot(args.api_key, args.api_secret, testnet=True)
            
            if args.type == 'MARKET':
                order = bot.place_market_order(args.symbol, args.side, args.quantity)
            elif args.type == 'LIMIT':
                if not args.price:
                    print("Price is required for limit orders")
                    return
                order = bot.place_limit_order(args.symbol, args.side, args.quantity, args.price)
            elif args.type == 'STOP_LIMIT':
                if not args.price or not args.stop_price:
                    print("Both price and stop-price are required for stop-limit orders")
                    return
                ticker = bot.client.futures_symbol_ticker(symbol=args.symbol.upper())
                current_price = float(ticker['price'])
                print(f"Current price: {current_price}")

                if args.side == 'BUY' and args.stop_price <= current_price:
                    print("Stop price must be ABOVE current price for a BUY stop-limit order")
                    return
                if args.side == 'SELL' and args.stop_price >= current_price:
                    print("Stop price must be BELOW current price for a SELL stop-limit order")
                    return
                order = bot.place_stop_limit_order(args.symbol, args.side, args.quantity, args.stop_price, args.price)
            
            bot.display_order_details(order)
            
        except Exception as e:
            print(f"Error: {e}")
    else:
        # Launch interactive CLI
        cli = TradingBotCLI()
        cli.main_menu()


if __name__ == "__main__":
    main()