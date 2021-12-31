from statsmodels.tsa.arima.model import ARIMA 
from System import *
from QuantConnect import *
from QuantConnect.Algorithm import *

class Algorithm_TBD(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2021, 1, 1)  # Set Start Date
        self.SetCash(100000)  # Set Strategy Cash
        self.EnableAutomaticIndicatorWarmUp = True
        self.securities_volu = ['AMD', 'ORCL', 'TSLA'] # Securities for high volume days
        self.securities_vold = ['JPM', 'V', 'XOM' ] # securities for low volume days
        self.keys_total = self.securities_volu + self.securities_vold
        self.daily_volatility = None
        
        # Add VIX  data.
        self.vix = self.AddEquity('VXX', Resolution.Daily) # ETF that has returns correlated to the VIX
        self.sma_vix = self.SMA(self.vix.Symbol, 3, Resolution.Daily, Field.Open) # opening price VIX SMA
        self.Schedule.On(self.DateRules.EveryDay(),self.TimeRules.At(9, 00),self.vix_selection)
        self.Schedule.On(self.DateRules.EveryDay(),self.TimeRules.At(15, 55),self.rebalance) # clear book
        
        for u, d in zip(self.securities_volu, self.securities_vold): # add all equities
            self.AddEquity(u, Resolution.Minute) 
            self.AddEquity(d, Resolution.Minute) 
            
            
        self.arima_col = {
                                    'amd' : self.ARIMA(self.securities_volu[0], 1, 1, 2, 50),# 50 period ARIMA
                                    'orcl' : self.ARIMA(self.securities_volu[1], 1, 1, 2, 50),
                                    'tsla' : self.ARIMA(self.securities_volu[2], 1, 1, 2, 50),
                                    'jpm' : self.ARIMA(self.securities_vold[0], 1, 1, 2, 50),
                                    'v' :self.ARIMA(self.securities_vold[1], 1, 1, 2, 50),
                                    'xom' :self.ARIMA(self.securities_vold[2], 1, 1, 2, 50)} 
                                    
        self.rsi_col_long = {
                                    'amd' : self.RSI(self.securities_volu[0], 6), # 6 period RSI
                                    'orcl' : self.RSI(self.securities_volu[1], 6),
                                    'tsla' : self.RSI(self.securities_volu[2], 6),
                                    'jpm' : self.RSI(self.securities_vold[0], 6),
                                    'v' : self.RSI(self.securities_vold[1], 6),
                                    'xom' : self.RSI(self.securities_vold[2], 6)}
        
        
    def OnData(self, data):
        # self.order_manager # Bracket for TP/SL using market orders
        if self.daily_volatility == 1:
            keys = [x.lower() for x in self.securities_volu]
            for k, v in zip(keys, self.securities_volu):
                if self.arima_col[k].Current.Value >= self.Securities[v].Price * 1.005 and not self.Portfolio[v].Invested and self.rsi_col_long[k].Current.Value <= 30:
                    quantity = self.CalculateOrderQuantity(v, 0.1666)
                    self.MarketOrder(v, quantity)
                else:
                    continue
        elif self.daily_volatility == 0:
            keys = [x.lower() for x in self.securities_vold]
            for k, v in zip(keys, self.securities_vold):
                if self.arima_col[k].Current.Value >= self.Securities[v].Price * 1.005 and not self.Portfolio[v].Invested and self.rsi_col_long[k].Current.Value <= 30:
                    quantity = self.CalculateOrderQuantity(v, 0.1666)
                    self.MarketOrder(v, quantity)
                else:
                    continue
        
    def vix_selection(self):
        if self.sma_vix.IsReady:
            if self.vix.Price > self.sma_vix.Current.Value:
                self.daily_volatility = 1
            elif self.vix.Price <= self.sma_vix.Current.Value:
                self.daily_volatility = 0
    
    # def order_manager(self):
    #     for k in self.keys_total:
    #         if self.Portfolio[k].Invested:
    #             if self.Portfolio[k].AveragePrice/self.Securities[k].Price < 0.97: # TP level
    #                 self.Liquidate(k)
    #                 self.Log('Take Profit Hit')
    #             elif self.Portfolio[k].AveragePrice/self.Securities[k].Price > 1.04: # SL level
    #                 self.Liquidate(k)
    #                 self.Log('Stop Loss Hit')
    
    def rebalance(self): # clear all positions
        for k in self.keys_total:
            if self.Portfolio[k].Invested:
                self.Liquidate(k)
