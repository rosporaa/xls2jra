#!/usr/bin/python3
# -*- coding: utf-8 -*-
# xls2jra - XLS to Jasmin REST API JSON
# - change values coding and country
# Coding  - use different coding page - accepted values 0, 4, 8 (0 -> GSM03.38, 4 -> 8-bit binary, 8 -> UCS2)
# Country - if not empty (""), check all numbers for prefix (example: country = "421") 
# Excel file format:
#  Only one column
#   1st row (A1):      Sender ID or phone number - max 11 chars, ONLY A-Z, a-z, 0-9, _, .
#   2nd row (A2):      SMS text
#   3rd and next rows: phone number - international format without +, example 421987123456
# Rows 1 and 2 are mandatory. Minimal one phone number is mandatory. Empty phone numbers(cells) will be skipped.
# Output in file sms_YYYYMMDDHHMMSS.json
# 2022 (c) ~Vlna~
# Requirements: python3, pandas for python

import json, sys, re, os
import unicodedata
from datetime import datetime
import pandas as pd
# with pandas you need to install xlrd
# if xlrd does not work (error: xlsx file not supported), install opepyxl and uncomment line below
from openpyxl.utils.exceptions import InvalidFileException


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
def perform(xlsfile, jsonfile, coding, restr, nodupl, verbose, testnumbers):
  js = {}
  onemessage = {}
  messages = []
  numbers = []
  isError = False
  ncount = 0
  insertrow = 0
  ntn = 0
  nullarray = []
  xlist = []

  # data_coding 0 -> GSM03.38,4 -> 8-bit binary, 8 -> UCS2
  onemessage = {"coding": coding, "from":"", "content":"", "to":""}

  # read xls[x] file in desired format
  # ONLY one column
  # 1st row - sender ID (or phone number), 
  # 2nd row - message (GSM03.38 chars, length max 256),
  # next row(s) - phone number to deliver message
  try:
    #df = pd.read_excel(xlsfile, header=None)
    df = pd.read_excel(xlsfile, header=None, engine='openpyxl')
  except ValueError as e:
    print (f" *Excel file format error: {str(e)}")
    sys.exit(3)
  except InvalidFileException as e:
    print (f" *Excel file format error: {str(e)}")
    sys.exit(3)

  # duplicity
  if nodupl == False:
    x = df.value_counts()
    xlist = x[x>1].index.tolist()
    if len(xlist) > 0:
      print (f" *Found duplicity: {str(xlist)}")
      sys.exit(7)

  maxrow = len(df.iloc[:, 0]) #df.index.stop #df.index[-1]  + 1
  # row 1 and 2 are mandatory, minimal 1 phone number is mandadory
  nullarray = df.isnull()
  natmp = nullarray
  countNotNULL = natmp[natmp[0] == False].count()

  if maxrow < 3:
    print (" *Incomplete excel file")
    sys.exit(5)

  # where to insert test numbers
  if (countNotNULL[0] - 2) > 12  and  testnumbers:          # minus 1st and second row
    insertrow = int((countNotNULL[0] - 2)/len(testnumbers))
    if verbose:
      print (f" - NonEpty rows: {countNotNULL[0]}, Test numbers: {len(testnumbers)}, Insert every: {insertrow}")

  for r in range (0, maxrow):
    strr = str(df.iloc[r, 0])
    
    # 1st row - sender ID -  (match) from O2
    if r == 0:
      if nullarray[0][r]:
        print (" *Error: 1st line empty!")
        sys.exit(6)
      x = re.match('^(?=.*[\.\w])(?=.*[a-zA-Z]).{0,11}$', strr)
      y = re.match('^421940682[0-9]{3}$', strr)
      if x == None  and  y == None:
        print (f" *Bad format sender ID: {strr}")
        isError = True
        continue
      onemessage['from'] = strr
      
    # 2nd row - message - max 254 characters, test coding
    if r == 1:
      if nullarray[0][r]:
        print (" *Error: 2st line empty!")
        sys.exit(6)

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

      if onemessage['coding'] == 4:          
        del (onemessage['content'])
        xtmp = unicodedata.normalize('NFKD', strr)
        onemessage['hex_content'] = xtmp.encode('ascii', 'ignore').hex()

        # other codepages:
        #   onemessage['hex_content'] = strr.encode('utf-8').hex()
        # back: strr = bytes.fromhex(hex_content).decode('utf-8')

      if onemessage['coding'] == 8:          
        del (onemessage['content'])
        onemessage['hex_content'] = strr.encode('utf-16-be').hex()

    # next rows - phone numbers
    if r > 1:  
      if nullarray[0][r]:
        continue

      x = re.match(restr, strr)
      if x == None:
        print (f" *Bad phone number: '{strr}'")
        isError = True
        continue

      numbers.append(strr)  
      # add testnumbers
      ncount += 1
      if testnumbers  and  len(testnumbers) > ntn  and  insertrow > 1  and  ncount%insertrow == 0:
        x = re.match(restr, testnumbers[ntn])
        if x != None:
          numbers.append(testnumbers[ntn])
          if verbose:
            print (f" - Adding test number, position {ncount + ntn + 1}: {testnumbers[ntn]}")
          ntn += 1

  if not ncount:
    print (" *No phone numbers found!")
    isError = True

  if isError == True:
    sys.exit(4)

  js['messages'] = ""
  onemessage['to'] = numbers
  messages.append(onemessage)

  js['messages'] = messages

  # create JSON file
  f = open(jsonfile, "w")
  json.dump(js, f, ensure_ascii=False)
  f.close()
  if verbose:
    print (f" - Output in file: {jsonfile}")


# MAIN
if __name__ == "__main__":
  nodupl = False
  verbose = False
  testnumbers = []

  # SET VALUES:
  # data_coding - acepted 0 -> GSM03.38, 4 -> 8-bit binary, 8 -> UCS2
  coding = 8
  # country - if not empty, check county prefix in phone numbers
  country = "421"


  if len(sys.argv) < 2:
    print (f"Usage: python {sys.argv[0]} xlsfile [--nodupl] [--verbose]")
    print (" --nodupl  - dont test duplicate phone numbers")
    print (" --verbose - print some informations")    
    print (" --tn:PHONENUM:PHONENUM - testing phone numbers, delimiter :")
    print ("\nXLS format: Only one column")
    print ("            1st row: Sender ID or phone number")
    print ("            2nd row: SMS text")
    print ("            3rd and next rows: phone number")
    print ("\nOutput in file sms_YYYYMMDDHHMMSS.json")
    print ("Recommendation: Validate output with jq")
    # jq .messages[].to[] sms_.json | wc -l
    # jq .messages[].content sms_.json
    # jq .messages[].from sms_.json
    sys.exit(1)

  if not os.path.exists(sys.argv[1]):
    print (f" *File '{sys.argv[1]}' does not exist")
    sys.exit(2)

  # test country in phone numbers - make regexp
  if len(country) > 0: 
    maxnumlen = 12 - len(country)
    restr = '^' + country + '[0-9]{' + str(maxnumlen) + '}$'
  else:
    restr = '^[0-9]{12}$'

  if "--nodupl" in sys.argv:
    nodupl = True

  if "--verbose" in sys.argv:
    verbose = True

  if verbose:
    print (f" - Country set to: '{country}'")
    print (f" - Coding set to:  {coding}")

  for sa in sys.argv:
    tn = re.search("--tn(:[0-9]{12})+", sa)
    if tn != None:
      tnx = tn.group().strip().split(':')
      for i in range(1, len(tnx)):
        # testing proper format
        x = re.match(restr, tnx[i])
        if x != None:
          testnumbers.append(tnx[i])
      if verbose:
        print (f" - Test numbers: {testnumbers}")
      break

  now = datetime.now()
  dtm = now.strftime("%Y%m%d%H%M%S")

  perform(sys.argv[1], f"sms_{dtm}.json", coding, restr, nodupl, verbose, testnumbers)
