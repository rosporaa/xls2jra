# xls2jra
xls2jra - XLS to Jasmin REST API, output JSON | 2022 (c) ~ Vlna ~  
Jasmin is an open-source SMS Gateway with many enterprise-class features (support HTTP and SMPP protocols).   

     
Usage: *python xls2jra.py xlsfile [--verbose] [--nodupl] [--tn PHONENUM [PHONENUM]] [--maxpn NUMBER] [--maxSMSlen NUMBER] [--dataCoding NUMBER] [--country NUMBER] [--url URL] [--auth AUTH] [--callback CALLBACKURL] [--errback ERRBACKURL]*    
-    --verbose - print more information        
-    --nodupl - don't test duplicate phone numbers        
-    --tn PHONENUM [PHONENUM ...] - test phone numbers         
-    --maxpn NUMBER - maximum number of phone numbers in output file = divide output to files          
-    --maxSMSlen NUMBER - maximum characters in message (default: 160)                   
-    --dataCoding NUMBER - message text coding (supported 0, 4, 8) (default: 8 - UCS2)                      
-    --country NUMBER - check country prefix          
-    --url URL - url (Jasmin's RESTAPI sendbatch) to send JSON (file(s))     
-    --auth AUTH - authorization data (base64 encoded string)  
-    --callback - callback url for successfuly sent messages   
-    --errback - callback url for unsuccessfuly sent messages   

XLS format:   
-  Only one column             
-  1st row: Sender ID or phone number                 
-  2nd row: SMS text              
-  3rd and next rows: phone number              

Output in file sms_YYYYMMDDHHMMSS.json  (or sms_YYYYMMDDHHMMSS_N.json with --maxpn option).               

# Tip  

Use --maxSMSlen 0 to show message text.  
Example:  
  *python xls2jra.py small_test.xls --nodupl --verbose --maxSMSlen 0*  
  
Output:  
 *\- Test duplicity:      False  
 \- Max. SMS length:     0  
 \- Check county prefix: No  
 \- Coding set to:       8  
 \*Message too long (36): 'Vitajte v našej skutočnej aplikácii!'  
 \*Found problems, resolve and try again*  

