# Import historical data from yfinance and estimate garch model
import yfinance as yf
import arch

company_stock = yf.download('AAPL',start='2023-05-01',end='2023-06-01')

daily_returns = company_stock['Close'].pct_change().dropna()

garch_model = arch.arch_model(daily_returns, vol='GARCH', p=1, o=0, q=1)
res = garch_model.fit(update_freq=5)
print(res.summary())

fig = res.plot()
plt.show()

# Connect to IBKR and retrieve information 
import pandas as pd
from ibapi.wrapper import EWrapper
from ibapi.client import EClient
from ibapi.contract import Contract
from datetime import datetime, timedelta
import random
import threading
import time

def generate_client_id():
    return random.randint(10000000, 99999999)

############################
# Call related to financial statement information
############################
client_id = generate_client_id()

class OptionDataWrapper(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.fundamental_data_received = False
        self.fundamental_data = None
        
    def connectionClosed(self):
        print("Connection closed.")
        
    def fundamentalData(self, reqId: int, data: str):
        print("Received Fundamental Data: ", data)
        self.fundamental_data = data
        self.fundamental_data_received = True


def main():

    global app
    global global_df  # Declare the global variable to update it from within the thread

    # Setup the connection
    app = OptionDataWrapper()
    
    try:
        app.connect("127.0.0.1", 4002, clientId=client_id)
        
        # Sleep for 10 seconds after making the connection
        time.sleep(10)

        contract = Contract()
        contract.symbol = "AAPL"
        contract.secType = "STK"
        contract.exchange = "SMART"
        contract.currency = "USD"
        
        app.reqFundamentalData(1, contract, "ReportsFinStatements", [])
        
        while not app.fundamental_data_received:
            app.run()  # Use app.run() to handle the event loop

        # Update the global variable with the populated dataframe
        global_df = app.fundamental_data

    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        app.disconnect()

# Wrap the main function in a thread
if __name__ == "__main__":
    app = None  # Initialize app as None
    t = threading.Thread(target=main)
    t.start()

    # Keep the script interactive
    while True:
        cmd = input("Enter 'stop' to stop the connection or 'exit' to quit: ").strip().lower()
        
        if cmd == 'stop':
            app.disconnect()  # Directly calling disconnect on the app object
            t.join()  # Wait for the thread to finish
            break

        elif cmd == 'exit':
            app.disconnect()  # Ensure the connection is stopped before exiting
            break


# Now, global_df holds the populated dataframe and can be used in the rest of your script
print(global_df)
print(global_last_price)
global_df.to_csv('dataframe.csv', index=False)
global_df = pd.read_csv('dataframe.csv')

############################
# Call related to options
############################
client_id = generate_client_id()

class OptionDataWrapper(EWrapper, EClient):

    def connectionClosed(self):
        print("Connection closed.")

    def __init__(self):
        EClient.__init__(self, self)  # Initialize the EClient part
        self.df = pd.DataFrame(columns=["Expiry", "Strike"])
        self.received_contract_details = None
        self.option_data_processed = False
        self.lastPrice = None

    def contractDetails(self, reqId, contractDetails):
        print(f"Received contract details for ReqID: {reqId}")
        print(contractDetails.contract.symbol, contractDetails.contract.secType, contractDetails.contract.currency)
        print(contractDetails.longName)
        print(contractDetails.underConId)
        # Save received contract details
        self.contract_details = contractDetails.contract
        # Make subsequent request using the saved details
        self.reqSecDefOptParams(2, underlyingSymbol=self.contract_details.symbol, 
                                futFopExchange="", 
                                underlyingSecType=self.contract_details.secType, 
                                underlyingConId=self.contract_details.conId)

    def securityDefinitionOptionParameter(self, reqId, exchange, underlyingConId, tradingClass, multiplier,
                                          expirations, strikes):
        
        if self.option_data_processed:
            # If data has already been processed before, just return
            return
        
        print("Received Option Data:")

        # Current date
        current_date = datetime.now()

        # Get the date six months from now
        six_months_later = current_date + timedelta(days=180)

        data = []
        for expiry in expirations:
            expiry_date = datetime.strptime(expiry, "%Y%m%d")

            # Only consider expiries less than six months away
            if expiry_date <= six_months_later:
                for strike in strikes:
                   data.append({"Expiry": expiry, "Strike": strike})

        self.df = pd.concat([self.df, pd.DataFrame(data)], ignore_index=True)

        # Set the flag to True after processing
        self.option_data_processed = True

    def tickPrice(self, reqId, tickType, price, attrib):
        if tickType == 4:  # Last trade price
            self.lastPrice = price
            print(f"Last trade price: {price}")

    def error(self, reqId, errorCode, errorString):
        print(f"Error: {reqId}, Code: {errorCode}, Msg: {errorString}")

    def stop_app(app):
        """Stops the IB event loop"""
        app.done = True
        app.disconnect()

def main():
    global app
    global global_df  # Declare the global variable to update it from within the thread
    global global_last_price

    # Setup the connection
    app = OptionDataWrapper()
    app.connect("127.0.0.1", 4002, clientId=client_id)

    # Sleep for 10 seconds after making the connection
    time.sleep(10)

    # Create a contract object for the underlying you're interested in
    contract = Contract()
    contract.symbol = "GLTO"
    contract.secType = "STK"
    contract.exchange = "SMART"
    contract.currency = "USD"

    # Check that contracts exist
    app.reqContractDetails(1, contract)

    #Get price quote of underlying
    app.reqMktData(3, contract, "", False, False, [])

    # Run the client event loop
    app.run()   

    # Update the global variable with the populated dataframe
    global_df = app.df
    global_last_price = app.lastPrice
    
# Wrap the main function in a thread
t = threading.Thread(target=main)

if __name__ == "__main__":
    t.start()

    # Keep the script interactive
    while True:
        cmd = input("Enter 'stop' to stop the connection or 'exit' to quit: ").strip().lower()
        
        if cmd == 'stop':
            app.disconnect()  # Directly calling disconnect on the app object
            t.join()  # Wait for the thread to finish
            break

        elif cmd == 'exit':
            app.disconnect()  # Ensure the connection is stopped before exiting
            break


# Now, global_df holds the populated dataframe and can be used in the rest of your script
print(global_df)
print(global_last_price)
global_df.to_csv('dataframe.csv', index=False)
global_df = pd.read_csv('dataframe.csv')
