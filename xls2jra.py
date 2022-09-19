#!/usr/bin/python3
# -*- coding: utf-8 -*-
# xls2jra - XLS to Jasmin REST API, JSON output
# Excel file format (input file):
#  Only one column
#   1st row (A1):      Sender ID or phone number - max 11 chars, ONLY A-Z, a-z, 0-9, _, .
#   2nd row (A2):      SMS text
#   3rd and next rows: phone number - international format without +, example 421987123456
# Rows 1 and 2 are mandatory. Minimal one phone number is mandatory. Empty phone numbers(cells) will be skipped.
# Output in file sms_YYYYMMDDHHMMSS.json
# With argument maxpn output will be divided to files sms_YYYYMMDDHHMMSS_N.json 
# 2022 (c) ~Vlna~
# Requirements: python3, pandas for python

import json, sys, re, os
import unicodedata
from datetime import datetime
import argparse
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
def perform(xlsfile, jsonfile, coding, restr, nodupl, verbose, testnumbers, maxsmslen, maxpn):
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
  # 2nd row - message, length max maxsmslen,
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
      
    # 2nd row - message - maxsmslen characters, test coding
    if r == 1:
      if nullarray[0][r]:
        print (" *Error: 2st line empty!")
        sys.exit(6)

      if len(strr) > maxsmslen:
        print (f" *Message too long ({len(strr)}): '{strr}'")
        isError = True

      if onemessage['coding'] == 0:
        c = test_gsm0338(strr)
        if not c:
          onemessage['content'] = strr
        else:
          print (f" *Bad character in message: {c}. (GSM03.38)")
          isError = True
      elif onemessage['coding'] == 4:          
        del (onemessage['content'])
        xtmp = unicodedata.normalize('NFKD', strr)
        onemessage['hex_content'] = xtmp.encode('ascii', 'ignore').hex()

        # other codepages:
        #   onemessage['hex_content'] = strr.encode('utf-8').hex()
        # back: strr = bytes.fromhex(hex_content).decode('utf-8')
      elif onemessage['coding'] == 8:          
        del (onemessage['content'])
        onemessage['hex_content'] = strr.encode('utf-16-be').hex()
      else:
        print (f" *Unsupported message coding: '{str(onemessage['coding'])}'")
        isError = True

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

  # divide output to files
  if maxpn > 0  and  len(numbers) > maxpn:
    fid = 0
    tmpnum = []
    for i in range(0, len(numbers)):
      if i > 0  and  i%maxpn == 0:
        js['messages'] = ""
        onemessage['to'] = tmpnum
        messages.append(onemessage)

        js['messages'] = messages

        # create JSON file
        f = open(jsonfile+"_"+ str(fid) +".json", "w")
        json.dump(js, f, ensure_ascii=False)
        f.close()
        if verbose:
          print (f" - Output in file: {jsonfile}_{str(fid)}.json")

        tmpnum = []
        onemessage['to'] = []
        messages = []
        fid = fid + 1

      tmpnum.append(numbers[i])      
    
    if len(tmpnum) > 0:  # last file
      js['messages'] = ""
      onemessage['to'] = tmpnum
      messages.append(onemessage)

      js['messages'] = messages

      # create JSON file
      f = open(jsonfile+"_"+ str(fid) +".json", "w")
      json.dump(js, f, ensure_ascii=False)
      f.close()
      if verbose:
        print (f" - Output in file: {jsonfile}_{str(fid)}.json")
  else:     # one output file
    js['messages'] = ""
    onemessage['to'] = numbers
    messages.append(onemessage)

    js['messages'] = messages

    # create JSON file
    f = open(jsonfile+".json", "w")
    json.dump(js, f, ensure_ascii=False)
    f.close()
    if verbose:
      print (f" - Output in file: {jsonfile}.json")


# MAIN
if __name__ == "__main__":
  nodupl = False
  verbose = False
  testnumbers = []
  maxpn = 0
  coding = 8       # default
  country = "421"  # default
  maxsmslen = 160  # default

  arg_epilog = """
  XLS format: Only one column
    1st row: Sender ID or phone number
    2nd row: SMS text
    3rd and next rows: phone number
  Output in file sms_YYYYMMDDHHMMSS.json
  Recommendation: Validate output with jq"""

  argp = argparse.ArgumentParser(description="XLS to Jasmin REST API, output JSON", epilog=arg_epilog, formatter_class=argparse.RawDescriptionHelpFormatter)
  argp.add_argument("xlsfile",      help="XLS filename")
  argp.add_argument("--nodupl",     help="Dont test duplicate phone numbers", action='store_true')
  argp.add_argument("--verbose",    help="Print more information", action='store_true')  
  argp.add_argument("--tn",         help="Testing phone numbers", nargs="+", type=int)  
  argp.add_argument("--maxpn",      help="Maximum number of phone numbers in output file = divide output to files", type=int, default=0)    
  argp.add_argument("--maxSMSlen",  help="Maximum characters in message (default: 160)", type=int, default=160)      
  argp.add_argument("--dataCoding", help="Data coding in SMS (supported 0, 4, 8) (default: 8 - UCS2)", type=int, default=8, choices=[0, 4, 8])      
  argp.add_argument("--country",    help="Country prefix number (default: 421)", type=str, default="421")      
  # jq .messages[].to[] sms_.json | wc -l
  # jq .messages[].content sms_.json
  # jq .messages[].from sms_.json

  allargs = argp.parse_args()

  if not os.path.exists(allargs.xlsfile):
    print (f" *File '{allargs.xlsfile}' does not exist")
    sys.exit(2)

  nodupl = allargs.nodupl
  verbose = allargs.verbose

  if allargs.tn:
    for i in allargs.tn:
      tn = re.search("[0-9]{12}", str(i))
      if tn != None:
        testnumbers.append(str(i))
      else:
        print (f" *Bad test number: {str(i)}, skiping ...")
    if verbose and len(testnumbers):
      print (f" - Test numbers: {testnumbers}")

  if allargs.maxpn:
    maxpn = allargs.maxpn
    if verbose:
      print (f" - Max. numbers in output: {maxpn}")

  maxsmslen = allargs.maxSMSlen
  coding = allargs.dataCoding
  country = allargs.country

  tn = re.search("^[0-9]{3}$", country)
  if tn == None:
    print (f" *Bad country prefix: {country}")
    sys.exit(9)

  if verbose:
    print (" - Test duplicity:  " + ("True" if not nodupl else "False") )
    print (f" - Max. SMS length: {maxsmslen}")
    print (f" - Country set to: '{country}'")
    print (f" - Coding set to:   {coding}")

  # test country in phone numbers - make regexp
  if len(country) > 0: 
    maxnumlen = 12 - len(country)
    restr = '^' + country + '[0-9]{' + str(maxnumlen) + '}$'
  else:
    restr = '^[0-9]{12}$'

  now = datetime.now()
  dtm = now.strftime("%Y%m%d%H%M%S")

  perform(allargs.xlsfile, f"sms_{dtm}", int(coding), restr, nodupl, verbose, testnumbers, int(maxsmslen), int(maxpn))