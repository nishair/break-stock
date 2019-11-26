import yfinance as yf

def main():
    data = yf.download('IBM','1999-11-18','2019-11-18')
    data.sort_values(by='Date')
    data['Opn_Close_diff'] = data.Open-data.Close
    data['High_Low_diff'] = data.High-data.Low
    data.to_excel('IBM.xlsx')
    data.pct_change()
    data.to_excel('IBM_Diff.xlsx')

if __name__ == '__main__'
    main()
