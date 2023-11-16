import sys
import time
import urllib.request
import json
from datetime import datetime, timedelta
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QAxContainer import *
from PyQt5.QtWidgets import *
import pandas as pd
import GiExpertControl as giLogin
import GiExpertControl as giJongmokTRShow
import GiExpertControl as giJongmokRealTime
from pythonUI import Ui_MainWindow

# 실시간 MA5, MA20, MA60 을 제공하기 위한 변수
today_vp = y_ma5 = y_ma20 = y_ma60 = yesterday_vp = 0

# 자동 트레이딩을 위한 변수
today_open_price = today_current_price = buy_qty = sell_qty = diff_ma5 = diff_ma20 = diff_ma60 = today_vp_min = today_vp_max = 0

# 주문하기 위한 flag
buy_flag = sell_flag = 0

# 폰트를 볼드체로 설정
font = QFont()
font.setBold(True)

# 2개의 실시간 데이터 받아오기
RTOCX1 = giJongmokRealTime.NewGiExpertModule()
RTOCX2 = giJongmokRealTime.NewGiExpertModule()

main_ui = Ui_MainWindow()

class indiWindow(QMainWindow):
    # UI 선언
    def __init__(self):
        super().__init__()
        self.setWindowTitle("IndiExample")
        giJongmokTRShow.SetQtMode(True)
        giJongmokTRShow.RunIndiPython()
        giLogin.RunIndiPython()
        giJongmokRealTime.RunIndiPython()

        self.rqidD = {}
        main_ui.setupUi(self)      

        main_ui.pushButton_getBalance.clicked.connect(self.pushButton_getBalance_clicked)
        main_ui.pushButton_getInfo.clicked.connect(self.pushButton_getInfo_clicked)
        # main_ui.pushButton_autoBuy.clicked.connect(self.pushButton_autoBuy_clicked)
        # main_ui.pushButton_autoSell.clicked.connect(self.pushButton_autoSell_clicked)

        # main_ui.pushButton_autoBuy.clicked.connect(self.pushButton_autoBuy2_clicked)
        # main_ui.pushButton_autoSell.clicked.connect(self.pushButton_autoSell2_clicked)

        main_ui.pushButton_autoBuy.clicked.connect(self.pushButton_autoBuy_test_clicked)
        main_ui.pushButton_autoSell.clicked.connect(self.pushButton_autoSell_test_clicked)

        giJongmokTRShow.SetCallBack('ReceiveData', self.giJongmokTRShow_ReceiveData) #데이터 조회

        RTOCX1.SetCallBack('ReceiveRTData', self.RTOCX1_ReceiveRTData) #실시간 데이터 - 등록개념
        RTOCX2.SetCallBack('ReceiveRTData', self.RTOCX2_ReceiveRTData) #실시간 데이터 - 등록개념

        print(giLogin.GetCommState())
        if giLogin.GetCommState() == 0: # 정상
            print("")        
        elif  giLogin.GetCommState() == 1: # 비정상
        #본인의 ID 및 PW 넣으셔야 합니다.
            login_return = giLogin.StartIndi('234109','test0365!','', 'C:\\SHINHAN-i\\indi\\GiExpertStarter.exe')
            if login_return == True:
                print("INDI 로그인 정보","INDI 정상 호출")
            else:
                print("INDI 로그인 정보","INDI 호출 실패")                    

    def pushButton_getBalance_clicked(self):
        acctNo_text = main_ui.plainTextEdit_acctNo.toPlainText()
        PW_text = main_ui.plainTextEdit_pwd.toPlainText()
        TR_Name = "SABA200QB"          
        ret = giJongmokTRShow.SetQueryName(TR_Name)          
        # print(giJongmokTRShow.GetErrorCode())
        # print(giJongmokTRShow.GetErrorMessage())
        ret = giJongmokTRShow.SetSingleData(0,acctNo_text)
        ret = giJongmokTRShow.SetSingleData(1,"01")
        ret = giJongmokTRShow.SetSingleData(2,PW_text)
        rqid = giJongmokTRShow.RequestData()
        print(type(rqid))
        print('Request Data rqid: ' + str(rqid))
        self.rqidD[rqid] = TR_Name

    def pushButton_getInfo_clicked(self):
        stbdCode_text = main_ui.plainTextEdit_stbdCode.toPlainText()
        
        # 종목명을 알아내기 위한 TR호출
        TR_Name = "stock_code"          
        ret = giJongmokTRShow.SetQueryName(TR_Name)          
        # print(giJongmokTRShow.GetErrorCode())
        # print(giJongmokTRShow.GetErrorMessage())
        ret = giJongmokTRShow.SetSingleData(0,stbdCode_text)
        rqid = giJongmokTRShow.RequestData()
        print(type(rqid))
        print('Request Data rqid: ' + str(rqid))
        self.rqidD[rqid] = TR_Name

        # # 체결강도 5일, 20일, 60일 이동평균선을 알아내기 위한 TR호출
        TR_Name = "TR_1843_S"          
        ret = giJongmokTRShow.SetQueryName(TR_Name)          
        # print(giJongmokTRShow.GetErrorCode())
        # print(giJongmokTRShow.GetErrorMessage())
        ret = giJongmokTRShow.SetSingleData(0,stbdCode_text)
        ret = giJongmokTRShow.SetSingleData(1,"61") # 61일간 데이터(전일대비 계산을 위해)
        rqid = giJongmokTRShow.RequestData()
        print('Request Data rqid: ' + str(rqid))
        self.rqidD[rqid] = TR_Name

        # 체결강도 및 체결 정보를 알아내기 위한 실시간 데이터 등록
        rqid = RTOCX1.RequestRTReg("SH",stbdCode_text)
        print(type(rqid))
        print('Request Data rqid: ' + str(rqid))

        rqid = RTOCX2.RequestRTReg("SC",stbdCode_text)
        print(type(rqid))
        print('Request Data rqid: ' + str(rqid))

    def pushButton_autoSell_test_clicked(self):
        global today_vp, today_open_price, today_current_price, buy_qty, sell_qty, diff_ma5, diff_ma20, diff_ma60

        # TR 셋팅
        acctNo_text = main_ui.plainTextEdit_acctNo.toPlainText()
        PW_text = main_ui.plainTextEdit_pwd.toPlainText()
        stbdCode_text = main_ui.plainTextEdit_stbdCode.toPlainText()
        qty_text = main_ui.plainTextEdit_qty.toPlainText()
        
        TR_Name = "SABA101U1"          
        ret = giJongmokTRShow.SetQueryName(TR_Name)
        ret = giJongmokTRShow.SetSingleData(0,acctNo_text)
        ret = giJongmokTRShow.SetSingleData(1,"01")
        ret = giJongmokTRShow.SetSingleData(2,PW_text)
        ret = giJongmokTRShow.SetSingleData(3,"")
        ret = giJongmokTRShow.SetSingleData(4,"")
        ret = giJongmokTRShow.SetSingleData(5,"0")
        ret = giJongmokTRShow.SetSingleData(6,"00")
        ret = giJongmokTRShow.SetSingleData(7,"1") # 매도=1 매수=2
        ret = giJongmokTRShow.SetSingleData(8,stbdCode_text)
        ret = giJongmokTRShow.SetSingleData(9,qty_text)
        ret = giJongmokTRShow.SetSingleData(10,"") # 가격
        ret = giJongmokTRShow.SetSingleData(11,"1")
        ret = giJongmokTRShow.SetSingleData(12,"1")
        ret = giJongmokTRShow.SetSingleData(13,"0")
        ret = giJongmokTRShow.SetSingleData(14,"0")
        ret = giJongmokTRShow.SetSingleData(15,"")
        ret = giJongmokTRShow.SetSingleData(16,"")
        ret = giJongmokTRShow.SetSingleData(17,"")
        ret = giJongmokTRShow.SetSingleData(18,"")
        ret = giJongmokTRShow.SetSingleData(19,"")
        ret = giJongmokTRShow.SetSingleData(20,"")
        ret = giJongmokTRShow.SetSingleData(21,"Y")
        rqid = giJongmokTRShow.RequestData()
    
        print(type(rqid))
        print('Request Data rqid: ' + str(rqid))
        self.rqidD[rqid] = TR_Name      
        
    def pushButton_autoSell_clicked(self):
        global buy_flag, sell_flag
        buy_flag = 1
        sell_flag = 0

    def pushButton_autoSell_clicked2(self):
        global today_vp, today_open_price, today_current_price, buy_qty, sell_qty, diff_ma5, diff_ma20, diff_ma60

        # TR 셋팅
        acctNo_text = main_ui.plainTextEdit_acctNo.toPlainText()
        PW_text = main_ui.plainTextEdit_pwd.toPlainText()
        stbdCode_text = main_ui.plainTextEdit_stbdCode.toPlainText()
        qty_text = main_ui.plainTextEdit_qty.toPlainText()
        
        TR_Name = "SABA101U1"          
        ret = giJongmokTRShow.SetQueryName(TR_Name)
        ret = giJongmokTRShow.SetSingleData(0,acctNo_text)
        ret = giJongmokTRShow.SetSingleData(1,"01")
        ret = giJongmokTRShow.SetSingleData(2,PW_text)
        ret = giJongmokTRShow.SetSingleData(3,"")
        ret = giJongmokTRShow.SetSingleData(4,"")
        ret = giJongmokTRShow.SetSingleData(5,"0")
        ret = giJongmokTRShow.SetSingleData(6,"00")
        ret = giJongmokTRShow.SetSingleData(7,"1") # 매도=1 매수=2
        ret = giJongmokTRShow.SetSingleData(8,"A"+ stbdCode_text)
        ret = giJongmokTRShow.SetSingleData(9,qty_text)
        ret = giJongmokTRShow.SetSingleData(10,"") # 가격
        ret = giJongmokTRShow.SetSingleData(11,"1")
        ret = giJongmokTRShow.SetSingleData(12,"1")
        ret = giJongmokTRShow.SetSingleData(13,"0")
        ret = giJongmokTRShow.SetSingleData(14,"0")
        ret = giJongmokTRShow.SetSingleData(15,"")
        ret = giJongmokTRShow.SetSingleData(16,"")
        ret = giJongmokTRShow.SetSingleData(17,"")
        ret = giJongmokTRShow.SetSingleData(18,"")
        ret = giJongmokTRShow.SetSingleData(19,"")
        ret = giJongmokTRShow.SetSingleData(20,"")
        ret = giJongmokTRShow.SetSingleData(21,"Y")

        # 무한루프 돌면서 조건 만족하면 매도진행
        print("## 자동 매수 시작 ##")
        while True :

            # 체결강도 100 이하인데, 양봉인 경우 매도함
            if (today_vp <= 100) and (today_open_price - today_current_price) < 0 :
                rqid = giJongmokTRShow.RequestData()
                break

            # 체결강도 100 이상이였는데, 100이하으로 하강돌파하고, 매수 잔량이 매도 잔량보다 많을 때 매도
            elif (today_vp_min <= 100) and (today_vp_max > 100) and (today_vp <= 100) and (buy_qty < sell_qty) :
                rqid = giJongmokTRShow.RequestData()
                break;
            
            # 체결강도 100 이상인데, 체결강도 이동평균선 5일, 20일, 60일이 모두 하강한 경우 매도
            elif (today_vp >= 100) and (diff_ma5 <= 0) and (diff_ma20 <=0) and (diff_ma60 <=0) :
                rqid = giJongmokTRShow.RequestData()
                break;
        
            time.sleep(1)  # 1초마다 주식 가격 확인
        
    
        print(type(rqid))
        print('Request Data rqid: ' + str(rqid))
        self.rqidD[rqid] = TR_Name    

    def pushButton_autoBuy_test_clicked(self):
        global today_vp, today_open_price, today_current_price, buy_qty, sell_qty, diff_ma5, diff_ma20, diff_ma60

        # TR 셋팅
        acctNo_text = main_ui.plainTextEdit_acctNo.toPlainText()
        PW_text = main_ui.plainTextEdit_pwd.toPlainText()
        stbdCode_text = main_ui.plainTextEdit_stbdCode.toPlainText()
        qty_text = main_ui.plainTextEdit_qty.toPlainText()
        
        TR_Name = "SABA101U1"          
        ret = giJongmokTRShow.SetQueryName(TR_Name)
        ret = giJongmokTRShow.SetSingleData(0,acctNo_text)
        ret = giJongmokTRShow.SetSingleData(1,"01")
        ret = giJongmokTRShow.SetSingleData(2,PW_text)
        ret = giJongmokTRShow.SetSingleData(3,"")
        ret = giJongmokTRShow.SetSingleData(4,"")
        ret = giJongmokTRShow.SetSingleData(5,"0")
        ret = giJongmokTRShow.SetSingleData(6,"00")
        ret = giJongmokTRShow.SetSingleData(7,"2") # 매도=1 매수=2
        ret = giJongmokTRShow.SetSingleData(8,"A"+ stbdCode_text)
        ret = giJongmokTRShow.SetSingleData(9,qty_text)
        ret = giJongmokTRShow.SetSingleData(10,"") # 가격
        ret = giJongmokTRShow.SetSingleData(11,"1")
        ret = giJongmokTRShow.SetSingleData(12,"1")
        ret = giJongmokTRShow.SetSingleData(13,"0")
        ret = giJongmokTRShow.SetSingleData(14,"0")
        ret = giJongmokTRShow.SetSingleData(15,"")
        ret = giJongmokTRShow.SetSingleData(16,"")
        ret = giJongmokTRShow.SetSingleData(17,"")
        ret = giJongmokTRShow.SetSingleData(18,"")
        ret = giJongmokTRShow.SetSingleData(19,"")
        ret = giJongmokTRShow.SetSingleData(20,"")
        ret = giJongmokTRShow.SetSingleData(21,"Y")
        rqid = giJongmokTRShow.RequestData()
    
        print(type(rqid))
        print('Request Data rqid: ' + str(rqid))
        self.rqidD[rqid] = TR_Name

    def pushButton_autoBuy_clicked(self):
        global buy_flag, sell_flag
        buy_flag = 0
        sell_flag = 1

    def pushButton_autoBuy2_clicked(self):
        global today_vp, today_open_price, today_current_price, buy_qty, sell_qty, diff_ma5, diff_ma20, diff_ma60

        # TR 셋팅
        acctNo_text = main_ui.plainTextEdit_acctNo.toPlainText()
        PW_text = main_ui.plainTextEdit_pwd.toPlainText()
        stbdCode_text = main_ui.plainTextEdit_stbdCode.toPlainText()
        qty_text = main_ui.plainTextEdit_qty.toPlainText()
        
        TR_Name = "SABA101U1"          
        ret = giJongmokTRShow.SetQueryName(TR_Name)
        ret = giJongmokTRShow.SetSingleData(0,acctNo_text)
        ret = giJongmokTRShow.SetSingleData(1,"01")
        ret = giJongmokTRShow.SetSingleData(2,PW_text)
        ret = giJongmokTRShow.SetSingleData(3,"")
        ret = giJongmokTRShow.SetSingleData(4,"")
        ret = giJongmokTRShow.SetSingleData(5,"0")
        ret = giJongmokTRShow.SetSingleData(6,"00")
        ret = giJongmokTRShow.SetSingleData(7,"2") # 매도=1 매수=2
        ret = giJongmokTRShow.SetSingleData(8,stbdCode_text)
        ret = giJongmokTRShow.SetSingleData(9,qty_text)
        ret = giJongmokTRShow.SetSingleData(10,"") # 가격
        ret = giJongmokTRShow.SetSingleData(11,"1")
        ret = giJongmokTRShow.SetSingleData(12,"1")
        ret = giJongmokTRShow.SetSingleData(13,"0")
        ret = giJongmokTRShow.SetSingleData(14,"0")
        ret = giJongmokTRShow.SetSingleData(15,"")
        ret = giJongmokTRShow.SetSingleData(16,"")
        ret = giJongmokTRShow.SetSingleData(17,"")
        ret = giJongmokTRShow.SetSingleData(18,"")
        ret = giJongmokTRShow.SetSingleData(19,"")
        ret = giJongmokTRShow.SetSingleData(20,"")
        ret = giJongmokTRShow.SetSingleData(21,"Y")

        # 무한루프 돌면서 조건 만족하면 매수진행
        print("## 자동 매수 시작 ##")
        while True :

            # 체결강도 100 이상인데, 음봉인 경우 매수함
            if (today_vp >= 100) and (today_open_price - today_current_price) > 0 :
                rqid = giJongmokTRShow.RequestData()
                break

            # 체결강도 100이하였는데, 100이상으로 상승돌파하고, 매도 잔량이 매수 잔량보다 많을 때 매수
            elif (today_vp_min < 100) and (today_vp_max >= 100) and (today_vp >= 100) and (buy_qty < sell_qty) :
                rqid = giJongmokTRShow.RequestData()
                break;
            
            # 체결강도 100 이하인데, 체결강도 이동평균선 5일, 20일, 60일이 상승한 경우 매수
            elif (today_vp < 100) and (diff_ma5 >= 0) and (diff_ma20 >=0) and (diff_ma60 >=0) :
                rqid = giJongmokTRShow.RequestData()
                break;
        
            time.sleep(1)  # 1초마다 주식 가격 확인
        
    
        print(type(rqid))
        print('Request Data rqid: ' + str(rqid))
        self.rqidD[rqid] = TR_Name      
        
    def pushButton_autoTrade_stop_clicked(self):
        global buy_flag, sell_flag
        buy_flag = 0
        sell_flag = 0

    def pushButton_2_clicked(self):      
        jongmokCode = main_ui.textEdit_3.toPlainText()
        rqid = giJongmokRealTime.RequestRTReg("SH",jongmokCode)
        print(type(rqid))
        print('Request Data rqid: ' + str(rqid))

    def pushButton_3_clicked(self):
        jongmokCode = main_ui.textEdit_3.toPlainText()
        ret = giJongmokRealTime.UnRequestRTReg("SH", jongmokCode) # 등록을 해지한다!
        print("ret : " + str(ret)) # 디버깅용

    def giJongmokTRShow_ReceiveData(self,giCtrl,rqid):
        print("in receive_Data:",rqid)
        print('recv rqid: {}->{}\n'.format(rqid, self.rqidD[rqid]))
        TR_Name = self.rqidD[rqid]

        print("TR_name : ",TR_Name)
        if TR_Name == "SABA200QB":
            nCnt = giCtrl.GetMultiRowCount()
            if nCnt != 0 : print("Get SABA200QB TR Result: ", nCnt)
            for i in range(0, nCnt):

                main_ui.tableWidget_acctInfo.setItem(i,0,QTableWidgetItem(str(giCtrl.GetMultiData(i, 0))))
                main_ui.tableWidget_acctInfo.setItem(i,1,QTableWidgetItem(str(giCtrl.GetMultiData(i, 1))))
                main_ui.tableWidget_acctInfo.setItem(i,2,QTableWidgetItem(str(giCtrl.GetMultiData(i, 2))))
                main_ui.tableWidget_acctInfo.setItem(i,3,QTableWidgetItem(str(giCtrl.GetMultiData(i, 5))))
                main_ui.tableWidget_acctInfo.setItem(i,4,QTableWidgetItem(str(giCtrl.GetMultiData(i, 6))))
                
                target_item_qty = main_ui.tableWidget_acctInfo.item(i,2)
                target_item_price = main_ui.tableWidget_acctInfo.item(i,3)
                target_item_mean = main_ui.tableWidget_acctInfo.item(i,4)

                target_item_qty.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                target_item_price.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)            
                target_item_mean.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
              

        elif TR_Name == "stock_code":
            nCnt = giCtrl.GetMultiRowCount()
            if nCnt != 0 : print("Get stock_code TR Result: ", nCnt)
            for i in range(0, nCnt):
                main_ui.tableWidget_stdbInfo.setItem(0,0,QTableWidgetItem(str(giCtrl.GetMultiData(0, 3)))) #종목명

            # 네이버 데이터랩 검색량
            client_id = "UdRf6rLBDCEIcWtAVzPf"
            client_secret = "KjN8zSfflO"
            url = "https://openapi.naver.com/v1/datalab/search";

            today = datetime.now().date()
            one_year_ago = today - timedelta(days=365)
            formatted_today_date = today.strftime("%Y-%m-%d")
            formatted_one_year_ago_date = one_year_ago.strftime("%Y-%m-%d")
            stbd_name = str(giCtrl.GetMultiData(0, 3))
            
            body = {
                "startDate":formatted_one_year_ago_date, 
                "endDate":formatted_today_date, 
                "timeUnit":"date", 
                "keywordGroups":[{
                    "groupName":"주식", 
                    "keywords":[stbd_name]
                    }], 
            }

            body = json.dumps(body, )

            request = urllib.request.Request(url)
            request.add_header("X-Naver-Client-Id",client_id)
            request.add_header("X-Naver-Client-Secret",client_secret)
            request.add_header("Content-Type","application/json")
            response = urllib.request.urlopen(request, data=body.encode("utf-8"))
            rescode = response.getcode()
            if(rescode==200):
                response_body = response.read()
                scraped = response_body.decode('utf-8')
            else:
                print("Error Code:" + rescode)

            result = json.loads(scraped)
            data = result['results'][0]['data'][-1]['ratio']
            print(int(data))

            main_ui.tableWidget_stdbInfo.setItem(0,1,QTableWidgetItem(str(int(data))))
            target_item_search = main_ui.tableWidget_stdbInfo.item(0, 1)
            target_item_search.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

        
        elif TR_Name == "TR_1843_S":
            nCnt = giCtrl.GetMultiRowCount()
            if nCnt != 0 : print("Get TR_1843_S TR Result", nCnt)

            df = pd.DataFrame(columns=['일자', '체결강도'])
            date = []
            VP = []
            for i in range(0,nCnt) :
                date.append(str(giCtrl.GetMultiData(i, 0)))
                VP.append(float(giCtrl.GetMultiData(i, 6)))

            for i in range(len(date)):
                df.loc[i] = [date[i], VP[i]]
            
            #print(df)
            
            # 실시간 체결강도 이평선 제공을 위한 저장
            global today_vp, y_ma5, y_ma20, y_ma60, yesterday_vp
            today_vp = df["체결강도"][0]
            yesterday_vp = df["체결강도"][1]
            # 체결강도 이평선 구하기
            #당일 체결강도 이평선
            MA_5 = df['체결강도'][:5].sum()/5
            MA_20 = df['체결강도'][:20].sum()/20
            MA_60 = df['체결강도'][:60].sum()/60

            #직전 영업일 체결강도 이평선
            Y_MA_5 = df['체결강도'][1:6].sum()/5
            Y_MA_20 = df['체결강도'][1:21].sum()/20
            Y_MA_60 = df['체결강도'][1:].sum()/60

            main_ui.tableWidget_stdbInfo.setItem(0,6,QTableWidgetItem(str(giCtrl.GetMultiData(0, 6)))) #체결강도
            main_ui.tableWidget_stdbInfo.setItem(0,7,QTableWidgetItem(str(round(MA_5, 2))))  #5일MA
            main_ui.tableWidget_stdbInfo.setItem(0,8,QTableWidgetItem(str(round(MA_20, 2)))) #20일MA
            main_ui.tableWidget_stdbInfo.setItem(0,9,QTableWidgetItem(str(round(MA_60, 2)))) #60일MA

            diff_MA5 = MA_5 - Y_MA_5
            diff_MA20 = MA_20 - Y_MA_20
            diff_MA60 = MA_60 - Y_MA_60

            y_ma5 = Y_MA_5
            y_ma20 = Y_MA_20
            y_ma60 = Y_MA_60

            main_ui.tableWidget_stdbInfo.setItem(1,7,QTableWidgetItem(str(round(diff_MA5, 2))))
            main_ui.tableWidget_stdbInfo.setItem(1,8,QTableWidgetItem(str(round(diff_MA20, 2))))
            main_ui.tableWidget_stdbInfo.setItem(1,9,QTableWidgetItem(str(round(diff_MA60, 2))))

            # 색상 변경을 위한 아이템 가져오기 및 TextAlign, Bold체 변경
            target_item_today = main_ui.tableWidget_stdbInfo.item(0, 6)
            target_item_MA5 = main_ui.tableWidget_stdbInfo.item(0, 7)
            target_item_MA20 = main_ui.tableWidget_stdbInfo.item(0, 8)
            target_item_MA60 = main_ui.tableWidget_stdbInfo.item(0, 9)
            target_item_diff_MA5 = main_ui.tableWidget_stdbInfo.item(1, 7)
            target_item_diff_MA20 = main_ui.tableWidget_stdbInfo.item(1, 8)
            target_item_diff_MA60 = main_ui.tableWidget_stdbInfo.item(1, 9)
            
            target_item_today.setFont(font)
            target_item_MA5.setFont(font)
            target_item_MA20.setFont(font)
            target_item_MA60.setFont(font)
            target_item_diff_MA5.setFont(font)
            target_item_diff_MA20.setFont(font)
            target_item_diff_MA60.setFont(font)

            target_item_today.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            target_item_MA5.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            target_item_MA20.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            target_item_MA60.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            target_item_diff_MA5.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            target_item_diff_MA20.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            target_item_diff_MA60.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            # 색상 변경 - 전일 대비 + 이면 빨간색, - 이면 파란색
            if diff_MA5 < 0 :
                target_item_diff_MA5.setForeground(QColor(0, 0, 255))
            else :
                target_item_diff_MA5.setForeground(QColor(255, 0, 0))

            if diff_MA20 < 0 :
                target_item_diff_MA20.setForeground(QColor(0, 0, 255))
            else :
                target_item_diff_MA20.setForeground(QColor(255, 0, 0))
            
            if diff_MA60 < 0 :
                target_item_diff_MA60.setForeground(QColor(0, 0, 255))
            else :
                target_item_diff_MA60.setForeground(QColor(255, 0, 0))

            if today_vp < yesterday_vp :
                target_item_today.setForeground(QColor(0, 0, 255))
            else :
                target_item_today.setForeground(QColor(255, 0, 0))
            # for i in range(0, nCnt):
            #     main_ui.tableWidget_stdbInfo.setItem(0,0,QTableWidgetItem(str(giCtrl.GetMultiData(0, 3))))
        
        elif TR_Name == "SABA101U1" :
            nCnt = giCtrl.GetSingleRowCount()
            print("nCnt: ", nCnt)
            if nCnt == 0 : 
                print("주문 실패")
            else :
                if str(giCtrl.GetSingleData(0)) == "0" :
                    print("주문 실패!!")
                else:
                    print("주문 성공!!")

        else:
            print("TR code ERROR")
        print("")

    def RTOCX1_ReceiveRTData(self,giCtrl,RealType):
        if RealType == "SH": # 현물 호가
            print("TR code: SH")
            #print(giJongmokTRShow.GetErrorCode())
            #print(giJongmokTRShow.GetErrorMessage())

            global buy_qty, sell_qty
            buy_qty =  int(giCtrl.GetSingleData(45))
            sell_qty =  int(giCtrl.GetSingleData(44))

            buy_qty_text = '{:,}'.format(buy_qty)
            sell_qty_text = '{:,}'.format(sell_qty)

            main_ui.tableWidget_stdbInfo.setItem(0,4,QTableWidgetItem(buy_qty_text)) #매수잔량
            main_ui.tableWidget_stdbInfo.setItem(0,5,QTableWidgetItem(sell_qty_text)) #매도잔량

            # CSS
            target_item_buyRest = main_ui.tableWidget_stdbInfo.item(0, 4)
            target_item_sellRest = main_ui.tableWidget_stdbInfo.item(0, 5)

            target_item_buyRest.setFont(font)
            target_item_sellRest.setFont(font)

            target_item_buyRest.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            target_item_sellRest.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            target_item_buyRest.setForeground(QColor(255, 0, 0))
            target_item_sellRest.setForeground(QColor(0, 0, 255))

        else:
            print("RT code ERROR")
        print("")

    def RTOCX2_ReceiveRTData(self,giCtrl,RealType):
        if RealType == "SC": # 현물 현재가
            print("TR code: SC")
            #print(giJongmokTRShow.GetErrorCode())
            #print(giJongmokTRShow.GetErrorMessage())

            global today_vp, y_ma5, y_ma20, y_ma60, today_open_price, today_current_price, diff_ma5, diff_ma20, diff_ma60, today_vp_min, today_vp_max, buy_flag, sell_flag

            today_open_price = int(giCtrl.GetSingleData(10))
            today_current_price = int(giCtrl.GetSingleData(3))

            buy_price =  int(giCtrl.GetSingleData(21))
            sell_price =  int(giCtrl.GetSingleData(20))            
            today_vp = float(giCtrl.GetSingleData(24))
            today_vp_min = today_vp if today_vp_min == 0 else min(today_vp, today_vp_min)
            today_vp_max = today_vp if today_vp_max == 0 else max(today_vp, today_vp_max)

            buy_price_text = '{:,}'.format(buy_price)
            sell_price_text = '{:,}'.format(sell_price)

            main_ui.tableWidget_stdbInfo.setItem(0,2,QTableWidgetItem(buy_price_text)) #매수1호가
            main_ui.tableWidget_stdbInfo.setItem(0,3,QTableWidgetItem(sell_price_text)) #매도1호가
            main_ui.tableWidget_stdbInfo.setItem(0,6,QTableWidgetItem(str(giCtrl.GetSingleData(24)))) #체결강도            

            current_MA5 = (float(main_ui.tableWidget_stdbInfo.item(0, 7).text()) * 5 - today_vp + float(giCtrl.GetSingleData(24))) / 5
            current_MA20 = (float(main_ui.tableWidget_stdbInfo.item(0, 8).text()) * 20 - today_vp + float(giCtrl.GetSingleData(24))) /20
            current_MA60 = (float(main_ui.tableWidget_stdbInfo.item(0, 9).text()) * 60 - today_vp + float(giCtrl.GetSingleData(24))) / 60

            #트레이딩 매수매도에 사용할 지표 저장
            diff_ma5 = current_MA5 - y_ma5
            diff_ma20 = current_MA20 - y_ma20
            diff_ma60 = current_MA60 - y_ma60

            item_MA5 = QTableWidgetItem(str(round(current_MA5, 2)))
            item_MA20 = QTableWidgetItem(str(round(current_MA20, 2)))
            item_MA60 = QTableWidgetItem(str(round(current_MA60, 2)))
            item_diff_MA5 = QTableWidgetItem(str(round(diff_ma5, 2)))
            item_diff_MA20 = QTableWidgetItem(str(round(diff_ma20, 2)))
            item_diff_MA60 = QTableWidgetItem(str(round(diff_ma60, 2)))

            main_ui.tableWidget_stdbInfo.setItem(0,7,item_MA5) #MA5
            main_ui.tableWidget_stdbInfo.setItem(0,8,item_MA20) #MA20
            main_ui.tableWidget_stdbInfo.setItem(0,9,item_MA60) #MA60
            main_ui.tableWidget_stdbInfo.setItem(1,7,item_diff_MA5) #MA5
            main_ui.tableWidget_stdbInfo.setItem(1,8,item_diff_MA20) #MA20
            main_ui.tableWidget_stdbInfo.setItem(1,9,item_diff_MA60) #MA60

            # CSS
            target_item_buyPrice = main_ui.tableWidget_stdbInfo.item(0, 2)
            target_item_sellPrice = main_ui.tableWidget_stdbInfo.item(0, 3)
            target_item_vp = main_ui.tableWidget_stdbInfo.item(0, 6)

            target_item_buyPrice.setFont(font)
            target_item_sellPrice.setFont(font)
            target_item_vp.setFont(font)

            target_item_buyPrice.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            target_item_sellPrice.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            target_item_vp.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            target_item_today = main_ui.tableWidget_stdbInfo.item(0, 6)
            target_item_MA5 = main_ui.tableWidget_stdbInfo.item(0, 7)
            target_item_MA20 = main_ui.tableWidget_stdbInfo.item(0, 8)
            target_item_MA60 = main_ui.tableWidget_stdbInfo.item(0, 9)
            target_item_diff_MA5 = main_ui.tableWidget_stdbInfo.item(1, 7)
            target_item_diff_MA20 = main_ui.tableWidget_stdbInfo.item(1, 8)
            target_item_diff_MA60 = main_ui.tableWidget_stdbInfo.item(1, 9)
            
            target_item_today.setFont(font)
            target_item_MA5.setFont(font)
            target_item_MA20.setFont(font)
            target_item_MA60.setFont(font)
            target_item_diff_MA5.setFont(font)
            target_item_diff_MA20.setFont(font)
            target_item_diff_MA60.setFont(font)

            target_item_today.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            target_item_MA5.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            target_item_MA20.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            target_item_MA60.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            target_item_diff_MA5.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            target_item_diff_MA20.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            target_item_diff_MA60.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            # 색상 변경 - 전일 대비 + 이면 빨간색, - 이면 파란색
            if current_MA5 - y_ma5 < 0 :
                target_item_diff_MA5.setForeground(QColor(0, 0, 255))
            else :
                target_item_diff_MA5.setForeground(QColor(255, 0, 0))

            if current_MA20 - y_ma20 < 0 :
                target_item_diff_MA20.setForeground(QColor(0, 0, 255))
            else :
                target_item_diff_MA20.setForeground(QColor(255, 0, 0))
            
            if current_MA60 - y_ma60 < 0 :
                target_item_diff_MA60.setForeground(QColor(0, 0, 255))
            else :
                target_item_diff_MA60.setForeground(QColor(255, 0, 0))

            if today_vp < yesterday_vp :
                target_item_today.setForeground(QColor(0, 0, 255))
            else :
                target_item_today.setForeground(QColor(255, 0, 0))

            # 주문 넣기!
            # TR 셋팅
            acctNo_text = main_ui.plainTextEdit_acctNo.toPlainText()
            PW_text = main_ui.plainTextEdit_pwd.toPlainText()
            stbdCode_text = main_ui.plainTextEdit_stbdCode.toPlainText()
            qty_text = main_ui.plainTextEdit_qty.toPlainText()
            TR_Name = "SABA101U1"          
            ret = giJongmokTRShow.SetQueryName(TR_Name)
            ret = giJongmokTRShow.SetSingleData(0,acctNo_text)
            ret = giJongmokTRShow.SetSingleData(1,"01")
            ret = giJongmokTRShow.SetSingleData(2,PW_text)
            ret = giJongmokTRShow.SetSingleData(3,"")
            ret = giJongmokTRShow.SetSingleData(4,"")
            ret = giJongmokTRShow.SetSingleData(5,"0")
            ret = giJongmokTRShow.SetSingleData(6,"00")
            ret = giJongmokTRShow.SetSingleData(8,"A"+ stbdCode_text)
            ret = giJongmokTRShow.SetSingleData(9,qty_text)
            ret = giJongmokTRShow.SetSingleData(10,"") # 가격
            ret = giJongmokTRShow.SetSingleData(11,"1")
            ret = giJongmokTRShow.SetSingleData(12,"1")
            ret = giJongmokTRShow.SetSingleData(13,"0")
            ret = giJongmokTRShow.SetSingleData(14,"0")
            ret = giJongmokTRShow.SetSingleData(15,"")
            ret = giJongmokTRShow.SetSingleData(16,"")
            ret = giJongmokTRShow.SetSingleData(17,"")
            ret = giJongmokTRShow.SetSingleData(18,"")
            ret = giJongmokTRShow.SetSingleData(19,"")
            ret = giJongmokTRShow.SetSingleData(20,"")
            ret = giJongmokTRShow.SetSingleData(21,"Y")
            
            # 매수
            if buy_flag == 1 :
                print("### 매수 대기중 ###")
                ret = giJongmokTRShow.SetSingleData(7,"2") # 매도=1 매수=2
                # 체결강도 100 이상인데, 음봉인 경우 매수함
                if (today_vp >= 100) and (today_open_price - today_current_price) > 0 :
                    rqid = giJongmokTRShow.RequestData()
                    buy_flag = 0
                    print("### 매수 완료 ###")

                # 체결강도 100이하였는데, 100이상으로 상승돌파하고, 매도 잔량이 매수 잔량보다 많을 때 매수
                elif (today_vp_min < 100) and (today_vp_max >= 100) and (today_vp >= 100) and (buy_qty < sell_qty) :
                    rqid = giJongmokTRShow.RequestData()
                    buy_flag = 0
                    print("### 매수 완료 ###")
                
                # 체결강도 100 이하인데, 체결강도 이동평균선 5일, 20일, 60일이 상승한 경우 매수
                elif (today_vp < 100) and (diff_ma5 >= 0) and (diff_ma20 >=0) and (diff_ma60 >=0) :
                    rqid = giJongmokTRShow.RequestData()
                    buy_flag = 0
                    print("### 매수 완료 ###")               

            # 매도    
            elif sell_flag == 1 :
                print("### 매도 대기중 ###")
                ret = giJongmokTRShow.SetSingleData(7,"1") # 매도=1 매수=2
                 # 체결강도 100 이하인데, 양봉인 경우 매도함
                if (today_vp <= 100) and (today_open_price - today_current_price) < 0 :
                    rqid = giJongmokTRShow.RequestData()
                    sell_flag = 0
                    print("### 매도 완료 ###")
                    
                # 체결강도 100 이상이였는데, 100이하으로 하강돌파하고, 매수 잔량이 매도 잔량보다 많을 때 매도
                elif (today_vp_min <= 100) and (today_vp_max > 100) and (today_vp <= 100) and (buy_qty < sell_qty) :
                    rqid = giJongmokTRShow.RequestData()
                    sell_flag = 0
                    print("### 매도 완료 ###")
                                    
                # 체결강도 100 이상인데, 체결강도 이동평균선 5일, 20일, 60일이 모두 하강한 경우 매도
                elif (today_vp >= 100) and (diff_ma5 <= 0) and (diff_ma20 <=0) and (diff_ma60 <=0) :
                    rqid = giJongmokTRShow.RequestData()
                    sell_flag = 0
                    print("### 매도 완료 ###")

        else:
            print("RT code ERROR")
        print("")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    IndiWindow = indiWindow()    
    IndiWindow.show()
    app.exec_()
    
    # if IndiWindow.MainSymbol != "":
    #     giJongmokRealTime.UnRequestRTReg("SH", "")