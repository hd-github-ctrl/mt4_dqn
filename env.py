# -*- coding: utf-8 -*-
from collections import deque
import random
import torch
import pandas as pd
from datetime import datetime, timedelta
import os


class Env():
  def __init__(self, mtapi,args,symbol, initial_balance=10000, transaction_cost=10, timeframe="H1",starttime=datetime.now()-timedelta(hours=2000),endtime=datetime.now()):
    self.device = args.device
    actions = {0:"buy",1:"sell"}
    self.actions = actions
    self.lives = 0  # Life counter (used in DeepMind training)
    self.life_termination = False  # Used to check if resetting only from loss of life
    self.window = args.history_length  # Number of frames to concatenate
    self.state_buffer = deque([], maxlen=args.history_length)
    self.training = True  # Consistent with model training mode
    self.symbol = symbol
    self.initial_balance = initial_balance
    self.balance = initial_balance
    self.holdings = 0
    self.win=0
    self.lose=0
 
    self.transaction_cost = transaction_cost
    self.data = None
    self.current_step = 100
    self.done = False
    self.mtapi =mtapi
    self.spread=2
    self.future_bar_count =24
    self.symbol_point=10000
    
    # Initialize mtapi connection with provided parameters
    
    if  self.mtapi is not None and self.mtapi.initialize():
        # Fetch historical data
        self._loadFromMTAPI(symbol, timeframe,starttime, endtime)
        self.data.to_json('./results/'+symbol+starttime.strftime('%Y%m%d%H%M')+'.json')
    else:
        file_path=self._get_random_json_file('./results')
        if file_path is None:
            print("No data received")
            return
        else:
            self.data = pd.read_json(file_path)  
    self.steps=self.data.shape[0]
  def _reset_buffer(self):
    for _ in range(self.window):
      self.state_buffer.append(torch.zeros(10, 6, device=self.device))
  def _get_random_json_file(self,directory):
      # 获取指定目录下所有 .json 文件
      json_files = [os.path.join(directory, file) for file in os.listdir(directory) 
                    if os.path.isfile(os.path.join(directory, file)) and file.endswith('.json')]
      
      # 随机选择一个 .json 文件
      if json_files:
          random_file = random.choice(json_files)
          return random_file
      else:
          return None
  def _loadFromMTAPI(self,symbol, timeframe,starttime, endtime):
      rates = self.mtapi.copy_rates_from(symbol, timeframe,starttime, endtime)
      if rates is None:
          print("No data received")
          self.mtapi.shutdown()
          return
      self.data = pd.DataFrame(rates)
      self.data['time'] = pd.to_datetime(self.data['time'], unit='s')
      self.data.set_index('time', inplace=True)
      self.data = self.data[['open', 'high', 'low', 'close', 'tick_volume']]
      self.data = self.data.astype(float)

      # Preprocess data
      self.data['returns'] = self.data['close'].diff()
      self.data['returns'].fillna(0, inplace=True)
      self.data['volume'] = self.data['tick_volume']
      # 初始化 futurehigh 和 futurehigh_index
      self.data['futurehigh'] = None
      self.data['futurehigh_index'] = None
      self.data['futurelow'] = None
      self.data['futurelow_index'] = None
    
      # Calculate SMA20 and SMA50
      self.data['SMA20'] = self.data['close'].rolling(window=20).mean()
      self.data['SMA50'] = self.data['close'].rolling(window=50).mean()

      # Calculate RSI
      delta = self.data['close'].diff()
      gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
      loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
      rs = gain / loss
      self.data['RSI'] = 100 - (100 / (1 + rs))

      # Normalize RSI
      self.data['RSI'] = (self.data['RSI'] - self.data['RSI'].min()) / (self.data['RSI'].max() - self.data['RSI'].min())

      # Calculate Bollinger Bands
      self.data['SMA20'] = self.data['close'].rolling(window=20).mean()
      self.data['std'] = self.data['close'].rolling(window=20).std()
      self.data['upper_band'] = self.data['SMA20'] + (self.data['std'] * 2)
      self.data['lower_band'] = self.data['SMA20'] - (self.data['std'] * 2)

  def _get_state(self,shift=0):
    current_price = self.data['close'].iloc[self.current_step-shift]
    volume = self.data['volume'].iloc[self.current_step-shift]
    volumemean = self.data['volume'].rolling(20).mean().iloc[self.current_step-shift]

    sma20 = self.data['SMA20'].iloc[self.current_step-shift]
    sma50 = self.data['SMA50'].iloc[self.current_step-shift]
    rsi = self.data['RSI'].iloc[self.current_step]
    upper_band = self.data['upper_band'].iloc[self.current_step-shift]
    lower_band = self.data['lower_band'].iloc[self.current_step-shift]
    bb_position = (current_price-lower_band)/(upper_band-lower_band)
    volume_position = volume/volumemean
    state=[
        current_price / sma20,  # Price to SMA20 ratio
        current_price / sma50,  # Price to SMA50 ratio
        rsi,  # Normalized RSI
        bb_position,  # Bollinger Band position
        volume_position,  # Volume ratio
        (current_price -self.data['close'].iloc[self.current_step-1-shift])/self.data['close'].iloc[self.current_step-1-shift]  # Price change ratio
    ]
    #state = cv2.resize(self.ale.getScreenGrayscale(), (84, 84), interpolation=cv2.INTER_LINEAR)
    return state
  def reset(self):
    self.current_step = torch.randint(100, self.steps-25, (1,)).item() 
    self.done = False
    self._reset_buffer()
    self.current_step-=3
    self.state_buffer.append(self.get_state())  
    self.current_step+=1
    self.state_buffer.append(self.get_state()) 
    self.current_step+=1
    self.state_buffer.append(self.get_state()) 
    self.current_step+=1
    self.state_buffer.append(self.get_state())
    return torch.stack(list(self.state_buffer), 0)
  
  def get_state(self):
      data=[]
      for i in range(9, -1, -1):
          data.append(self._get_state(i))  
      #data = [[[element for element in row] for row in data]]    
      return torch.tensor(data, dtype=torch.float32, device=self.device)
  def cal_reward(self,action,shift=0):

      if self.current_step + self.future_bar_count > len(self.data):
          future_bar_count=len(self.data)-self.current_step
      else:
          future_bar_count=self.future_bar_count
      current_step=self.current_step
      current_price = self.data['close'].iloc[self.current_step]
      if action==0:       
          future_values = self.data['high'].iloc[self.current_step + 1:self.current_step + future_bar_count]  # 当前行之后的 24 行
          if future_values.empty or future_values.isnull().all():
            print("未来值为空或全部为 NaN")
            reward=0
            done=True
            return reward,done  # 或者根据需要处理这个异常
          max_value = future_values.max()  # 获取最大值
          max_index = self.data.index.get_loc(future_values.idxmax())  # 获取最大值的索引
          maxprofit=(max_value-current_price)*self.symbol_point*self.transaction_cost/(max_index-self.current_step)
          future_values = self.data['low'].iloc[self.current_step + 1:self.current_step+ future_bar_count]  # 当前行之后的 24 行
          min_value = future_values.min()  # 获取最小值
          min_index = self.data.index.get_loc(future_values.idxmin())  # 获取最小值的索引  
          minprofit= (min_value-current_price)*self.symbol_point*self.transaction_cost/(min_index-self.current_step)   
          reward=maxprofit+minprofit
          done=True
      if action==1: 
          future_values = self.data['high'].iloc[self.current_step + 1:self.current_step + future_bar_count]  # 当前行之后的 24 行
          if future_values.empty or future_values.isnull().all():
            print("未来值为空或全部为 NaN")
            reward=0
            done=True
            return reward,done  # 或者根据需要处理这个异常
          max_value = future_values.max()  # 获取最大值
          max_index = self.data.index.get_loc(future_values.idxmax())  # 获取最大值的索引
          maxprofit=(current_price-max_value)*self.symbol_point*self.transaction_cost/(max_index-self.current_step)
          future_values = self.data['low'].iloc[self.current_step + 1:self.current_step + future_bar_count]  # 当前行之后的 24 行
          min_value = future_values.min()  # 获取最小值
          min_index = self.data.index.get_loc(future_values.idxmin())  # 获取最小值的索引  
          minprofit= (current_price-min_value)*self.symbol_point*self.transaction_cost/(min_index-self.current_step)   
          reward=maxprofit+minprofit
          done=True
      if action==2:
          reward=0
          done=True
      return reward,done
  def step(self, action):
    if self.done:
        return torch.stack(list(self.state_buffer), 0),0, True

    reward,done=self.cal_reward(action)
    self.done=done
    self.balance += reward
    if reward > 0:
        self.win+=1
    if reward < 0:
        self.lose+=1
    if(self.win+self.lose==0):
        self.holdings=0
    else:
      self.holdings = self.win/(self.win+self.lose)
    self.current_step += 1
    if self.current_step >= len(self.data) - 1:
        self.done = True
    self.state_buffer.append(self.get_state())
    state = torch.stack(list(self.state_buffer), 0)
    return state, reward, self.done

  # Uses loss of life as terminal signal
  def train(self):
    self.training = True

  # Uses standard terminal signal
  def eval(self):
    self.training = False

  def action_space(self):
    return len(self.actions)

  def render(self):
    pass

  def close(self):
    #self.mtapi.shutdown()
    pass
