import smtplib 
from email.mime.multipart import MIMEMultipart 
from email.mime.text import MIMEText 
from email.mime.application import MIMEApplication 
import datetime
today = datetime.date.today()
import os

def send_mail(a,b,c,send_time):
    _pwd = "mima"            #这里一定要用第三方授权的密码而不是登陆密码
    _to  = c      #注意这里不要用qq邮箱，负责下载文件时会乱码
    _user = a
    
    #如名字所示Multipart就是分多个部分 
    msg = MIMEMultipart() 
    msg["Subject"] = "【{0}】期现套利盘口提醒。".format(today)
    msg["From"]  = _user 
    msg["To"]   = _to 
       
    #---这是文字部分--- 
    # part = MIMEText("【{0}】期现套利盘口提醒。".format(today) )
    part = MIMEText("触发时间【{0}】。\n".format(send_time) )
    msg.attach(part)  
    #---这是附件部分--- 
    #xlsx类型附件 
    part1 = MIMEApplication(open('to_be_sent.csv'.format(today),'rb').read(),'utf-8') 
    part1.add_header('Content-Disposition', 'attachment', filename='./result/to_be_sent.csv'.format(today))    
    msg.attach(part1) 

    s = smtplib.SMTP_SSL(b, timeout=10,port=465)#连接smtp邮件服务器,端口默认是25 
    s.login(_user, _pwd)#登陆服务器 
    s.sendmail(_user, _to, msg.as_string())#发送邮件 
    #s.sendmail(_user, _to1, msg.as_string())#发送邮件 
   
    s.close()

send_mail("case@163.com","smtp.163.com",'case@163.com',today)



