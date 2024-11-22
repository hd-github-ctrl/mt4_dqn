import socketserver
import time
import inspect
import threading
import ctypes
import pandas as pd
import json
class MT4():
    """
    Setup socket -> MetaTrader Connector
    """

    def __init__(self,
                 _host='localhost',         # Host to connect to
                 _port=8888,
                 _comment='python-to-mt',
                 _magic=123456):         # 1 ms for time.sleep()
        self.comment=_comment
        self.magic=_magic
        self.server = socketserver.ThreadingTCPServer((_host, _port), MyHandler)
        self.server.connected=False
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        # Exit the server thread when the main thread terminates
        self.server_thread.daemon = True
        self.server_thread.start()
    def initialize(self):
        try:
            self.server.connected=False
            msg=self.heartbeart()
            if msg.find("OK")>=0:	
                self.server.connected=True
                return True
        except:
            pass  
        return False
    def shutdown(self):
        self.server.RequestHandlerClass.is_running=False

    def remote_send(self,msg):
        #if self.server.connected!=True :
        #    print("MT4 connection falled!!!")
          #  raise Exception("MT4 connection falled!!!")
        self.server.RequestHandlerClass.trades["result"] = ""
        self.server.RequestHandlerClass.trades["action"] = msg
        retry=0
        while self.server.RequestHandlerClass.trades["result"]=="":
            if retry>5:
                raise Exception("MT4 connection falled!!!")
            self.server.RequestHandlerClass.trades["action"] = msg
            time.sleep(1)
            retry=retry+1
        return self.server.RequestHandlerClass.trades["result"].replace("'","\"")
    def stop(self):
        stop_thread(self.server_thread)
    def getPrice(self,_symbol):
        _msg = "{};{};\r\n".format('DATA', _symbol)
        return self.remote_send(_msg)
    """
    Function to construct messages for sending Trade commands to MetaTrader
    """
    def buy(self,_symbol,_lot,_sl=0,_tp=0):
        return self.trade('OPEN',0,_symbol,0,_sl,_tp,self.comment,_lot,self.magic,0)
    def sell(self,_symbol,_lot,_sl=0,_tp=0):
        return self.trade('OPEN',1,_symbol,0,_sl,_tp,self.comment,_lot,self.magic,0)
    def buylimit(self,_symbol,_lot,_price,_sl=0,_tp=0):
        return self.trade('OPEN',2,_symbol,_price,_sl,_tp,self.comment,_lot,self.magic,0)
    def selllimit(self,_symbol,_lot,_price,_sl=0,_tp=0):
        return self.trade('OPEN',3,_symbol,_price,_sl,_tp,self.comment,_lot,self.magic,0)
    def buystop(self,_symbol,_lot,_price,_sl=0,_tp=0):
        return self.trade('OPEN',4,_symbol,_price,_sl,_tp,self.comment,_lot,self.magic,0)
    def sellstop(self,_symbol,_lot,_price,_sl=0,_tp=0):
        return self.trade('OPEN',5,_symbol,_price,_sl,_tp,self.comment,_lot,self.magic,0)
    def close(self,_ticket):
        return self.trade('CLOSE', 0, '', 0, 0, 0, self.comment, 0, self.magic, _ticket)  # 关闭订单
    def closepartial(self,_ticket,_lot):
        return self.trade('CLOSE_PARTIAL', 0, '', 0, 0, 0, self.comment,_lot, self.magic, _ticket)  # 部分关闭订单
    def closeall(self):
        return self.trade('CLOSE_ALL', 0, '', 0, 0, 0, self.comment, 0, self.magic, 0)    # 关闭所有订单
    '''
       获取所有持仓，不含挂单
    '''
    def getorders(self):
        return self.trade('GET_OPEN_TRADES',0,'',0,0,0,self.comment,0,self.magic,0)  #获取所有开仓
    '''
      获取账户信息，返回账户的信息，包含账户名称,余额，净值等
    '''
    def getaccount(self):
        return self.trade('GET_ACCOUNT_INFO',0,'',0,0,0,self.comment,0,self.magic,0) #获取账户信息
    '''
      修改订单
        _ticket:订单编号
        _sl,_tp:止损,止盈 的点数（相对开单价格的点数）
    '''
    def modify(self,_ticket,_sl,_tp): #修改订单
        return self.trade('MODIFY',0,'',0,_sl,_tp,self.comment,0,self.magic,_ticket) #修改订单
    def copy_rates_from(self, _symbol, _timeframe, _start_datetime, _end_datetime):
        _msg = "{};{};{};{};{}\r\n".format('TRACK_RATES', _symbol, _timeframe, _start_datetime, _end_datetime)
        json_rates= self.remote_send(_msg) #获取历史数据
        result=json.loads(json_rates)
        if len(result.get("_response"))>1:
            return pd.json_normalize(data=result,record_path=["_response"])
        return None
    def heartbeart(self):
        return self.remote_send("HEARTBEAT\r\n") #heartbeat ping
    
    
    def trade(self, _action='OPEN', _type=0,
                               _symbol='EURUSD', _price=0.0,
                               _SL=50, _TP=50, _comment="Python-to-MT",
                               _lots=0.01, _magic=123456, _ticket=0):

        _msg = "{};{};{};{};{};{};{};{};{};{};{}\r\n".format('TRADE', _action, _type,
                                                         _symbol, _price,
                                                         _SL, _TP, _comment,
                                                         _lots, _magic,
                                                         _ticket)


        return self.remote_send(_msg)


        """
         compArray[0] = TRADE or DATA
         compArray[1] = ACTION (e.g. OPEN, MODIFY, CLOSE,CLOSE_PARTIAL,CLOSE_MAGIC,CLOSE_ALL,GET_OPEN_TRADES,GET_ACCOUNT_INFO)
         compArray[2] = TYPE (e.g. OP_BUY, OP_SELL, etc - only used when ACTION=OPEN)

         For compArray[0] == DATA, format is: 
             DATA|SYMBOL|TIMEFRAME|START_DATETIME|END_DATETIME

         // ORDER TYPES: 
         // https://docs.mql4.com/constants/tradingconstants/orderproperties

         // OP_BUY = 0
         // OP_SELL = 1
         // OP_BUYLIMIT = 2
         // OP_SELLLIMIT = 3
         // OP_BUYSTOP = 4
         // OP_SELLSTOP = 5

         compArray[3] = Symbol (e.g. EURUSD, etc.)
         compArray[4] = Open/Close Price (ignored if ACTION = MODIFY)
         compArray[5] = SL
         compArray[6] = TP
         compArray[7] = Trade Comment
         compArray[8] = Lots
         compArray[9] = Magic Number
         compArray[10] = Ticket Number (MODIFY/CLOSE)
         """
        # pass

class MyHandler(socketserver.BaseRequestHandler):
    """ BaseRequestHandler的实例化方法中，获得了三个属性
    self.request = request  # 该线程中与客户端交互的 socket 对象。
    self.client_address   # 该线程处理的客户端地址
    self.server = server   # 服务器对象
    """
    trades ={"action":"","result":""}
    lock = threading.Lock()
    is_running = True
    #def setup(self):
        # super().setup()
        # self.server.connected=True
    def handle(self):
        while self.is_running:
            if self.trades["action"]!="":
                with self.lock:
                   self.trades["result"] =""
                   blockmsg=b''
                   self.request.send(self.trades["action"].encode())  # 将消息发送客户端
                time.sleep(0.5)
                try:
                  msg = self.request.recv(1024)  # 接受客户端的数据
                except:
                  msg=b''
                while len(msg)==1024:
                    blockmsg=blockmsg+msg
                    msg = self.request.recv(1024)  # 接受客户端的数据
                if msg == b'':  # 退出
                    continue

                blockmsg=blockmsg+msg
                with self.lock:
                    self.trades["action"] =""
                    self.trades["result"] = str(blockmsg,encoding="utf8")
    def finish(self):
        self.request.close()  # 关闭套接字
       # self.server.connected=False
def _async_raise(tid, exctype):
    """raises the exception, performs cleanup if needed"""
    tid = ctypes.c_long(tid)
    if not inspect.isclass(exctype):
        exctype = type(exctype)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
    if res == 0:
        raise ValueError("invalid thread id")
    elif res != 1:
        # """if it returns a number greater than one, you're in trouble,
        # and you should call it again with exc=NULL to revert the effect"""
        ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
        raise SystemError("PyThreadState_SetAsyncExc failed")
def stop_thread(thread):
    _async_raise(thread.ident, SystemExit)


