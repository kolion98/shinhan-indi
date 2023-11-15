import sys
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QAxContainer import *
from PyQt5.QtWidgets import *
import pandas as pd
import GiExpertControl as giLogin
import GiExpertControl as giJongmokTRShow
import GiExpertControl as giJongmokRealTime
from pythonUI import Ui_MainWindow

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
        main_ui.pushButton_autoBuy.clicked.connect(self.pushButton_autoBuy_clicked)
        main_ui.pushButton_autoSell.clicked.connect(self.pushButton_autoSell_clicked)

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

        # 체결강도 5일, 20일, 60일 이동평균선을 알아내기 위한 TR호출
        TR_Name = "TR_1843_S"          
        ret = giJongmokTRShow.SetQueryName(TR_Name)          
        # print(giJongmokTRShow.GetErrorCode())
        # print(giJongmokTRShow.GetErrorMessage())
        ret = giJongmokTRShow.SetSingleData(0,stbdCode_text)
        ret = giJongmokTRShow.SetSingleData(1,"61") # 61일간 데이터(전일대비 계산을 위해)
        rqid = giJongmokTRShow.RequestData()
        print(type(rqid))
        print('Request Data rqid: ' + str(rqid))
        self.rqidD[rqid] = TR_Name

        # 체결강도 및 체결 정보를 알아내기 위한 실시간 데이터 등록
        rqid = RTOCX1.RequestRTReg("SH",stbdCode_text)
        print(type(rqid))
        print('Request Data rqid: ' + str(rqid))

        rqid = RTOCX2.RequestRTReg("SC",stbdCode_text)
        print(type(rqid))
        print('Request Data rqid: ' + str(rqid))

    def pushButton_autoSell_clicked(self):
        acctNo_text = main_ui.plainTextEdit_stbdCode.toPlainText()
        TR_Name = "stock_code"          
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
        
    def pushButton_2_clicked(self):      
        jongmokCode = main_ui.textEdit_3.toPlainText()
        rqid = giJongmokRealTime.RequestRTReg("SH",jongmokCode)
        print(type(rqid))
        print('Request Data rqid: ' + str(rqid))

    def pushButton_3_clicked(self):
        jongmokCode = main_ui.textEdit_3.toPlainText()
        ret = giJongmokRealTime.UnRequestRTReg("SH", jongmokCode) # 등록을 해지한다!
        print("ret : " + str(ret)) # 디버깅용

    def pushButton_autoBuy_clicked(self):
        jongmokCode = main_ui.textEdit_3.toPlainText()
        TR_Name = "SABA200QB"          
        ret = giJongmokTRShow.SetQueryName(TR_Name)          
        # print(giJongmokTRShow.GetErrorCode())
        # print(giJongmokTRShow.GetErrorMessage())
        ret = giJongmokTRShow.SetSingleData(0,gaejwa_text)
        ret = giJongmokTRShow.SetSingleData(1,"01")
        ret = giJongmokTRShow.SetSingleData(2,PW_text)
        rqid = giJongmokTRShow.RequestData()
        print(type(rqid))
        print('Request Data rqid: ' + str(rqid))
        self.rqidD[rqid] = TR_Name         
        
    def giJongmokTRShow_ReceiveData(self,giCtrl,rqid):
        print("in receive_Data:",rqid)
        print('recv rqid: {}->{}\n'.format(rqid, self.rqidD[rqid]))
        TR_Name = self.rqidD[rqid]
        tr_data_output = []
        output = []

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

        elif TR_Name == "stock_code":
            nCnt = giCtrl.GetMultiRowCount()
            if nCnt != 0 : print("Get stock_code TR Result: ", nCnt)
            for i in range(0, nCnt):
                main_ui.tableWidget_stdbInfo.setItem(0,0,QTableWidgetItem(str(giCtrl.GetMultiData(0, 3)))) #종목명
        
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

            main_ui.tableWidget_stdbInfo.setItem(1,7,QTableWidgetItem(str(round(diff_MA5, 2))))
            main_ui.tableWidget_stdbInfo.setItem(1,8,QTableWidgetItem(str(round(diff_MA20, 2))))
            main_ui.tableWidget_stdbInfo.setItem(1,9,QTableWidgetItem(str(round(diff_MA60, 2))))

            target_item_diff_MA5 = main_ui.tableWidget_stdbInfo.item(1, 7)
            target_item_diff_MA20 = main_ui.tableWidget_stdbInfo.item(1, 8)
            target_item_diff_MA60 = main_ui.tableWidget_stdbInfo.item(1, 9)
            
            # 색상 변경 - 전일 대비 + 이면 빨간색, - 이면 파란색
            if diff_MA5 < 0 :
                target_item_diff_MA5.setForeground(0, 0, 255)
            else :
                target_item_diff_MA5.setForeground(255, 0, 0)

            if diff_MA20 < 0 :
                target_item_diff_MA20.setForeground(0, 0, 255)
            else :
                target_item_diff_MA20.setForeground(255, 0, 0)
            
            if diff_MA60 < 0 :
                target_item_diff_MA60.setForeground(0, 0, 255)
            else :
                target_item_diff_MA60.setForeground(255, 0, 0)

            # for i in range(0, nCnt):
            #     main_ui.tableWidget_stdbInfo.setItem(0,0,QTableWidgetItem(str(giCtrl.GetMultiData(0, 3))))
        

        else:
            print("TR code ERROR")
        print("")

    def RTOCX1_ReceiveRTData(self,giCtrl,RealType):
        if RealType == "SH": # 현물 호가
            print("TR code: SH")
            #print(giJongmokTRShow.GetErrorCode())
            #print(giJongmokTRShow.GetErrorMessage())
            main_ui.tableWidget_stdbInfo.setItem(0,4,QTableWidgetItem(str(giCtrl.GetSingleData(45)))) #매수잔량
            main_ui.tableWidget_stdbInfo.setItem(0,5,QTableWidgetItem(str(giCtrl.GetSingleData(44)))) #매도잔량

        else:
            print("RT code ERROR")
        print("")

    def RTOCX2_ReceiveRTData(self,giCtrl,RealType):
        if RealType == "SC": # 현물 현재가
            print("TR code: SC")
            #print(giJongmokTRShow.GetErrorCode())
            #print(giJongmokTRShow.GetErrorMessage())
            main_ui.tableWidget_stdbInfo.setItem(0,2,QTableWidgetItem(str(giCtrl.GetSingleData(21)))) #매수1호가
            main_ui.tableWidget_stdbInfo.setItem(0,3,QTableWidgetItem(str(giCtrl.GetSingleData(20)))) #매도1호가
            main_ui.tableWidget_stdbInfo.setItem(0,6,QTableWidgetItem(str(giCtrl.GetSingleData(24)))) #체결강도

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