from flask import Flask, jsonify, request
import yfinance as yf

app = Flask(__name__)

def get_financials(ticker):
    stock = yf.Ticker(ticker)
    financials = {}
    
    # Income Statement
    income_statement = stock.financials
    income_statement_annual = income_statement.T
    
    # Convert Timestamps to strings
    income_statement_annual.index = income_statement_annual.index.strftime('%Y-%m-%d')
    financials['income_statement'] = income_statement_annual.to_dict()
    
    # Balance Sheet
    balance_sheet = stock.balance_sheet
    balance_sheet_annual = balance_sheet.T
    
    # Convert Timestamps to strings
    balance_sheet_annual.index = balance_sheet_annual.index.strftime('%Y-%m-%d')
    financials['balance_sheet'] = balance_sheet_annual.to_dict()
    
    return financials

@app.route('/financials/<ticker>', methods=['GET'])
def financials(ticker):
    try:
        financial_data = get_financials(ticker)
        return jsonify(financial_data)
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(debug=True)
