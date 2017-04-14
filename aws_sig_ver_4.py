#------------------------------------------
#--- Author: Pradeep Singh
#--- Date: 2nd April 2017
#--- Version: 1.0
#--- Python Ver: Python 2.7
#--- Description: This code will generate HTTP Request Headers, with AWS Signature 4 Authorization Header.
#---
#--- Refer to the following document for detailed information about AWS Sig 4 for REST API Calls
#--- http://docs.aws.amazon.com/general/latest/gr/sigv4_signing.html#sigv4_signing-steps-summary
#------------------------------------------


import base64, datetime, hashlib, hmac

# ==================================================================
# Anything after "?" in URL
Http_Query_String = ""
# Selected hashing algorithm
Algorithm = 'AWS4-HMAC-SHA256'
# AWS Service Name. Use "iotdata" for shadow operations.
AWS_Service_Name = "iotdata"
# Content Type
Content_Type_Header = "application/x-amz-json-1.0"
# ==================================================================


# DATE VALUES FOR HEADERS AND CREDENTIAL STRINGS
TimeValue = datetime.datetime.utcnow()
Amz_Date = TimeValue.strftime('%Y%m%dT%H%M%SZ')
Date_Stamp = TimeValue.strftime('%Y%m%d') # Date w/o time, used in credential scope

# FUNCTION TO SIGN THE INFORMATION
def sign(key, msg):
    return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()

# FUNCTION TO GENERATE SIGNATURE KEY
def getSignatureKey(key, dateStamp, regionName, serviceName):
    Signed_Date = sign(('AWS4' + key).encode('utf-8'), dateStamp)
    Signed_Region = sign(Signed_Date, regionName)
    Signed_Service = sign(Signed_Region, serviceName)
    Signature_Key = sign(Signed_Service, 'aws4_request')
    return Signature_Key

# Function to Generate AWS Signature 4 Authorization header
def get_Authorization_Header(Http_Method, IoT_Endpoint, AWS_Region, Shadow_URI, Access_Key, Secret_Key, Http_Request_Payload):
	# Prepare headers for signing.
	Http_Request_Headers = 'content-type:' + Content_Type_Header + '\n' + 'host:' + IoT_Endpoint + '\n' + 'x-amz-date:' + Amz_Date + '\n'
	# List of hearders we are going to sign
	Http_Request_Signed_Headers = 'content-type;host;x-amz-date'

	# TASK 1: CREATE A CANONICAL REQUEST FOR SIGNATURE VERSION 4
	# Details:  http://docs.aws.amazon.com/general/latest/gr/sigv4-create-canonical-request.html
	# Create Payload Hash
	Http_Request_Payload_Hash = hashlib.sha256(Http_Request_Payload).hexdigest()
	# Combine everything to create the Request
	Http_Request = Http_Method + '\n' +  Shadow_URI + "\n" + Http_Query_String + "\n" + Http_Request_Headers + '\n' + Http_Request_Signed_Headers + '\n' + Http_Request_Payload_Hash

	# TASK 2: CREATE A STRING TO SIGN FOR SIGNATURE VERSION 4
	# Details:  http://docs.aws.amazon.com/general/latest/gr/sigv4-create-string-to-sign.html
	# Create Credential Scope 
	Credential_Scope = Date_Stamp + '/' + AWS_Region + '/' + AWS_Service_Name + '/' + 'aws4_request' 
	# Create a String to Sign for Signature Version 4 
	String_To_Sign = Algorithm + '\n' +  Amz_Date + '\n' +  Credential_Scope + '\n' +  hashlib.sha256(Http_Request).hexdigest()

	# TASK 3: CALCULATE THE SIGNATURE FOR AWS SIGNATURE VERSION 4 
	# Details:  http://docs.aws.amazon.com/general/latest/gr/sigv4-calculate-signature.html
	# Create the signing key using the function defined above.
	Signing_Key = getSignatureKey(Secret_Key, Date_Stamp, AWS_Region, AWS_Service_Name)
	# Get AWS4 Signature using String_To_Sign created in Task 2
	AWS4_Signature = hmac.new(Signing_Key, (String_To_Sign).encode('utf-8'), hashlib.sha256).hexdigest()

	# TASK 4: ADD THE SIGNING INFORMATION TO THE REQUEST
	# Details:  http://docs.aws.amazon.com/general/latest/gr/sigv4-add-signature-to-request.html
	Authorization_Header = Algorithm + ' ' + 'Credential=' + Access_Key + '/' + Credential_Scope + ', ' +  'SignedHeaders=' + Http_Request_Signed_Headers + ', ' + 'Signature=' + AWS4_Signature

	return Authorization_Header

# Function to generate list of HTTP Request Headers
def get_HTTP_Request_Header(Http_Method, IoT_Endpoint, AWS_Region, Shadow_URI, Access_Key, Secret_Key, Http_Request_Payload):
	# Get Authorization Header
	HTTP_Authorization_Header = get_Authorization_Header(Http_Method, IoT_Endpoint, AWS_Region, Shadow_URI, Access_Key, Secret_Key, Http_Request_Payload)
	# Prepare HTTP Headers for Request 
	HTTP_Headers = {'content-type': Content_Type_Header, 'host': IoT_Endpoint, 'x-amz-date': Amz_Date, 'Authorization': HTTP_Authorization_Header}
	# Return Headers
	return HTTP_Headers
