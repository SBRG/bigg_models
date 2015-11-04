#!/usr/bin/env python

from ome.base import Session
from ome.models import (Model, Component, Reaction,Compartment, Metabolite,
                    CompartmentalizedComponent, ModelReaction, ReactionMatrix,
                    GeneReactionMatrix, ModelCompartmentalizedComponent, ModelGene,
                    Gene, Comments, GenomeRegion, Genome)
import datetime
import argparse
import smtplib

parser = argparse.ArgumentParser(description='input email information')
parser.add_argument('-u', '--user', help='Input user email', required=True)
parser.add_argument('-p', '--password', help='Input email password', required=True)
args = parser.parse_args()
session = Session()
current_time = datetime.datetime.now()
week_ago = current_time - datetime.timedelta(weeks=1)
comments = session.query(Comments).filter(Comments.date_created >  week_ago).all()
gmail_user = args.user
gmail_pwd = args.password
smtpserver = smtplib.SMTP("smtp.gmail.com", 587)
smtpserver.ehlo()
smtpserver.starttls()
smtpserver.login(gmail_user, gmail_pwd)
complete_msg = ""
header = ('To:' + gmail_user + '\n' + 'From: ' + 'BiGG notification system' + '\n' +
          'Subject:BiGG comment notification\n')
for c in comments:
    msg = 'Type: ' + c.type +'\n' + 'Body: ' + c.text + '\n' + 'From: ' + c.email
    complete_msg += msg
complete_msg = header + complete_msg
smtpserver.sendmail(gmail_user, gmail_user, complete_msg)
smtpserver.close()
