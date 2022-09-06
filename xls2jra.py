#/sbin/python
# -*- coding: utf-8 -*-
# xls2jra - XLS to Jasmin REST API JSON
# - change values coding, country and testnumbers
# Coding  - use different coding page - values 0, 4, 8 (0 -> GSM03.38,4 -> 8-bit binary, 8 -> UCS2)
# Country - if not empty (""), check all numbers for prefix (example: country = "421") 
# Testnumbers - insert testnumbers (international format without +) between numbers from excel to check delivery (idea by. Maros)
# Excel file format:
#  Only one column
#   1st row (A1):      Sender ID or phone number - max 11 chars, ONLY A-Z, a-z, 0-9, _, .
#   2nd row (A2):      SMS text
#   3rd and next rows: phone number - international format without +, example 421944123456
# Output in file sms_YYYYMMDDHHMMSS.json
# 2022 (c) ~Vlna~
# Requirements: python3, pandas for python

import json, sys, re, os
from datetime import datetime
import pandas as pd
# with pandas you need to install xlrd
# if xlrd does not work (error: xlsx file not supported), install opepyxl and uncomment line below
#from openpyxl.utils.exceptions import InvalidFileException


# test GSM03.38 characters in message
def test_gsm0338(text):
  gsm0338 = '@£$¥èéùìòÇ\nØø\rÅåΔ_ΦΓΛΩΠΨΣΘΞ\x1bÆæßÉ !"#¤%&\'()*+,-./0123456789:;<=>?¡ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜ§¿abcdefghijklmnopqrstuvwxyzäöñüà'

  # simple
  #x = re.match('[a-zA-Z0-9 !-%,=:;\*\+\.\?<>\(\)\/]+', text)
  #if x == None:
  #  return True

  for i in text:
    if i not in gsm0338:
      return i

  return False


# perform all actions
def main(xlsfile, jsonfile, coding, country):
  js = {}
  onemessage = {}
  messages = []
  numbers = []
  isError = False
  ncount = insertrow = ntn = 0
  testnumbers = ["421111111111", "421111111111", "421111111111"]

  # data_coding 0 -> GSM03.38,4 -> 8-bit binary, 8 -> UCS2
  onemessage = {"coding": coding, "from":"", "content":"", "to":""}

  # test country in phone numbers
  if len(country) > 0: 
    maxnumlen = 12 - len(country)
    restr = '^' + country + '[0-9]{' + str(maxnumlen) + '}$'
  else:
    restr = '^[0-9]{12}$'

  # read xls[x] file in desired format
  # ONLY one column
  # 1st row - sender ID (or phone number), 
  # 2nd row - message (GSM03.38 chars, length max 256),
  # next row(s) - phone number to deliver message
  try:
    df = pd.read_excel(xlsfile, header=None)
    # df = pd.read_excel(xlsfile, header=None, engine='openpyxl')
  except ValueError as e:
    print (f" *Excel file format error: {str(e)}")
    sys.exit(3)
  except InvalidFileException as e:
    print (f" *Excel file format error: {str(e)}")
    sys.exit(3)

  maxrow = df.index[-1]  + 1

  if maxrow < 3:
    print (" *Incomplete excel file")
    sys.exit(5)

  for r in range (0, maxrow):
    if maxrow > 10  and  testnumbers:
      insertrow = int(maxrow/len(testnumbers))
    strr = df.iloc[r, 0]
    
    # 1st row - sender ID -  (match) from O2
    if r == 0:
      x = re.match('^(?=.*[\.\w])(?=.*[a-zA-Z]).{0,11}$', strr)
      y = re.match('^421940682[0-9]{3}$', strr)
      if x == None  and  y == None:
        print (f" *Bad format sender ID: {strr}")
        isError = True
        continue
      onemessage['from'] = strr
      
    # 2nd row - message - max 254 characters, test coding
    if r == 1:
      if len(strr) > 254:
        print (f" *Message too long ({len(strr)}): '{strr}'")
        isError = True

      if onemessage['coding'] == 0:
        c = test_gsm0338(strr)
        if not c:
          onemessage['content'] = strr
        else:
          print (f" *Bad character in message: {c}. (GSM03.38)")
          isError = True

      #if onemessage['coding'] == 4:          
      #  del (onemessage['content'])
      #  onemessage['hex_content'] = strr.encode('utf-8').hex()
        # back: strr = bytes.fromhex(hex_content).decode('utf-8')

      if onemessage['coding'] == 4  or  onemessage['coding'] == 8:          
        del (onemessage['content'])
        onemessage['hex_content'] = strr.encode('utf-16-be').hex()

    # next rows - phone numbers
    if r > 1:  
      x = re.match(restr, strr)
      if x == None:
        print (f" *Bad phone number: '{strr}'")
        isError = True
        continue
      numbers.append(strr)  
      # add testnumbers
      ncount += 1
      if testnumbers  and  insertrow  and  not ncount%insertrow:
        x = re.match(restr, testnumbers[ntn])
        if x != None  and  testnumbers[ntn]:
          numbers.append(testnumbers[ntn])
          ntn += 1

  if isError == True:
    sys.exit(4)

  js['messages'] = ""
  onemessage['to'] = numbers
  messages.append(onemessage)

  # change data and add next message
  #onemessage = {"from":"TEST SMS2", "content":"TEst SMS type 2", "to":""}
  #numbers = []
  #numbers.append("CISLOOOOOO")
  #onemessage['to'] = numbers
  #messages.append(onemessage)

  js['messages'] = messages

  # create JSON file
  f = open(jsonfile, "w")
  json.dump(js, f, ensure_ascii=False)
  f.close()
  #print (f" *Output in file: {jsonfile}")


# MAIN
if __name__ == "__main__":
  if len(sys.argv) < 2:
    print (f"Usage: python {sys.argv[0]} xlsfile")
    print ("XLS format: Only one column")
    print ("            1st row: Sender ID or phone number")
    print ("            2nd row: SMS text")
    print ("            3rd and next rows: phone number")
    print ("Output in file sms_YYYYMMDDHHMMSS.json")
    print ("Recommendation: Validate output with jq")
    # jq .messages[].to[] sms_.json | wc -l
    # jq .messages[].content sms_.json
    # jq .messages[].from sms_.json
    sys.exit(1)

  if not os.path.exists(sys.argv[1]):
    print (f" *File '{sys.argv[1]}' does not exist")
    sys.exit(2)
     
  now = datetime.now()
  dtm = now.strftime("%Y%m%d%H%M%S")

  # data_coding 0 -> GSM03.38,4 -> 8-bit binary, 8 -> UCS2
  coding = 8
  # country - if not empty, check county prefix in phone numbers
  country = "421"
  
  main(sys.argv[1], f"sms_{dtm}.json", coding, country)
