#!/usr/bin/env python
from email.MIMEText import MIMEText
import httplib
import argparse
import smtplib


"""
if webpage returns 404 then email me
"""

parser = argparse.ArgumentParser(description='input email information')
parser.add_argument('-u', '--user', help='Input user email', required=True)
parser.add_argument('-p', '--password', help='Input email password', required=True)
args = parser.parse_args()
gmail_user = args.user
gmail_pwd = args.password
smtpserver = smtplib.SMTP("smtp.gmail.com", 587)
smtpserver.ehlo()
smtpserver.starttls()
smtpserver.login(gmail_user, gmail_pwd)
header = ('To:' + gmail_user + '\n' + 'From: ' + 'BiGG notification system' + '\n' +
          'Subject:BiGG comment notification\n')
error_complete_msg = 'The bigg.ucsd.edu website is down'
normal_complete_msg = "The bigg.ucsd.edu website is up"
#final_complete_msg = header + complete_msg
#smtpserver.sendmail(gmail_user, gmail_user, final_complete_msg  )
#smtpserver.close()
host = "bigg.ucsd.edu"
path = "/"
connect = httplib.HTTPConnection(host)
connect.request("HEAD", path)
if connect.getresponse().status == 404:
    final_complete_msg = header + error_complete_msg
    smtpserver.sendmail(gmail_user, gmail_user, final_complete_msg  )
    smtpserver.close()
