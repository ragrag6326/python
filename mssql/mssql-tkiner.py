import pyodbc
from tkinter import *
import time

def test():
    user = user_entey.get()
    user_list = user.split()
    userlong = len(user_list) -1

    upper = upper_entey.get()
    upper_list = user.split()
    Upperlong = len(upper_list) -1


    count = 0
    while userlong >= count and Upperlong >= count :
        # print(f'下級{user_list[count]} , 新上級{upper_list[count]}')
        result.config(text=f"下級{user_list[count]} , 新上級{upper_list[count]}")
        # time.sleep(2)
        count += 1  



window = Tk()

window.title('綁定名單修改')
window.geometry("500x600")
window.resizable(False,False)

message = Label(text="輸入下級" , font=("Terminal" , 20))
message.pack(side="top" )

# 按鈕
user_button = Button(text="確認" , font=("Terminal" , 15) , command=test)
user_button.pack(pady=10)

# 輸入欄
user_entey = Entry(width=50)
user_entey.pack(pady=10)
user_entey.get()

upper_entey = Entry(width=50)
upper_entey.pack(pady=10)
upper_entey.get()


result = Label(text="回傳結果" , font=("Terminal" , 20))
result.pack(side="bottom" )




window.mainloop()



def conn_db():
    # 連到 SQL Server
    DB_DRIVER = '{SQL Server}'
    SERVER = ''
    DATABASE = ''
    UID = ''
    PWD = ''

    conn = pyodbc.connect(f'DRIVER={DB_DRIVER};SERVER={SERVER};DATABASE={DATABASE};UID={UID};PWD={PWD}')

    # 自動執行script
    conn.autocommit = True

    # 創建執行對象
    cursor = conn.cursor()


    print ('範例 : 51713368 24190646')
    UsrID = input("請輸入原下級 , 多個請用空格分隔：\n")
    UsrIDs = UsrID.split()
    usrlong = len(UsrIDs) -1


    print ('範例 : 18294891 24485868')
    UpperUserID = input("請輸入新上級 , 多個請用空格分隔：\n")
    UpperUserIDs = UpperUserID.split()
    Upperlong = len(UpperUserIDs) -1


    count = 0
    while usrlong >= count and Upperlong >= count :

        # 執行 script
        cursor.execute("""
        DECLARE @Result int
        DECLARE @RtnValue VARCHAR(50)
        DECLARE @UserID INT
        DECLARE @UpperUserID INT
        SET @UserID = {UsrID}
        SET @UpperUserID = {UpperUserID}
        EXEC Backend.ChangeUpperAgent
            @UserID  = @UserID,
            @UpperUserID = @UpperUserID,
            @Result  = @Result OUTPUT,
            @RtnValue = @RtnValue OUTPUT
        SELECT @Result, @RtnValue
        """.format(UsrID=UsrIDs[count] ,UpperUserID=UpperUserIDs[count] ))


        # 獲取輸出參數
        result = cursor.fetchall()

        for row in result:
            try :
                Result = row[0]
                RtnValue = row[1]
                if Result == 1 :
                    print(f'{UsrIDs[count]} {RtnValue}')
                else:
                    raise Exception
            except:
                print(f'{UsrIDs[count]} {RtnValue}')

        count += 1

    # 關閉DB
    conn.close()