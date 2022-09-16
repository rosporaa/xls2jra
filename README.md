# xls2jra
xls2jra - XLS to Jasmin REST API, output JSON   
Jasmin is an open-source SMS Gateway with many enterprise-class features (support HTTP and SMPP protocols).
     
Usage: *python xls2jra.py xlsfile [--nodupl] [--verbose] [--tn:PHONENUM:PHONENUM] [--maxpn:NUMBER] [--maxSMSlen:NUMBER] [--dataCoding:NUMBER] [--country:NUMBER]*    
-    --nodupl - dont test duplicate phone numbers        
-    --verbose - print some informations        
-    --tn:PHONENUM:PHONENUM - testing phone numbers, delimiter :         
-    --maxpn:NUMBER - maximum number of phone numbers in output file = divide output to files          
-    --maxSMSlen:NUMBER - maximum characters in message (default: 160)                   
-    --dataCoding:NUMBER - data coding in SMS (supported 0, 4, 8) (default: 8 - UCS2)                      
-    --country:NUMBER - country prefix number (default: 421)                     

XLS format:   
-  Only one column             
-  1st row: Sender ID or phone number                 
-  2nd row: SMS text              
-  3rd and next rows: phone number              

Output in file sms_YYYYMMDDHHMMSS.json  (or sms_YYYYMMDDHHMMSS_N.json with --maxpn option).               
