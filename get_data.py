import yfinance as yf
import matplotlib.pyplot as plt

data = yf.download('IBM','1999-11-18','2019-11-18')

data.Close.plot()
plt.show()
