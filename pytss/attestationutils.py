#!/usr/bin/env python3

import uuid
import pyasn1
import hashlib
import os
import struct
import base64

from cryptography import exceptions as crypto_exceptions
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import (
    padding,
    rsa,
)
from cryptography.hazmat.primitives.ciphers import (
    algorithms,
    Cipher,
    modes,
)
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    PublicFormat,
)

from pytss import TspiContext
from tspi_defines import *
import tspi_exceptions

well_known_secret = bytearray([0] * 20)
srk_uuid = uuid.UUID('{00000000-0000-0000-0000-000000000001}')

trusted_certs = { "STM1": """-----BEGIN CERTIFICATE-----
MIIDzDCCArSgAwIBAgIEAAAAATANBgkqhkiG9w0BAQsFADBKMQswCQYDVQQGEwJD
SDEeMBwGA1UEChMVU1RNaWNyb2VsZWN0cm9uaWNzIE5WMRswGQYDVQQDExJTVE0g
VFBNIEVLIFJvb3QgQ0EwHhcNMDkwNzI4MDAwMDAwWhcNMjkxMjMxMDAwMDAwWjBV
MQswCQYDVQQGEwJDSDEeMBwGA1UEChMVU1RNaWNyb2VsZWN0cm9uaWNzIE5WMSYw
JAYDVQQDEx1TVE0gVFBNIEVLIEludGVybWVkaWF0ZSBDQSAwMTCCASIwDQYJKoZI
hvcNAQEBBQADggEPADCCAQoCggEBAJQYnWO8iw955vWqakWNr3YyazQnNzqV97+l
Qa+wUKMVY+lsyhAyOyXO31j4+clvsj6+JhNEwQtcnpkSc+TX60eZvLhgZPUgRVuK
B9w4GUVyg/db593QUmP8K41Is8E+l32CQdcVh9go0toqf/oS/za1TDFHEHLlB4dC
joKkfr3/hkGA9XJaoUopO2ELt4Otop12aw1BknoiTh1+YbzrZtAlIwK2TX99GW3S
IjaCi+fLoXyK2Fmx8vKnr9JfNL888xK9BQfhZzKmbKm/eLD1e1CFRs1B3z2gd3ax
pW5j1OIkSBMOIUeip5+7xvYo2gor5mxatB+rzSvrWup9AwIcymMCAwEAAaOBrjCB
qzAdBgNVHQ4EFgQU88kVdKbnc/8TvwxrrXp7Zc8ceCAwHwYDVR0jBBgwFoAUb+bF
bAe3bIsKgZKDXMtBHva00ScwRQYDVR0gAQH/BDswOTA3BgRVHSAAMC8wLQYIKwYB
BQUHAgEWIWh0dHA6Ly93d3cuc3QuY29tL1RQTS9yZXBvc2l0b3J5LzAOBgNVHQ8B
Af8EBAMCAAQwEgYDVR0TAQH/BAgwBgEB/wIBADANBgkqhkiG9w0BAQsFAAOCAQEA
uZqViou3aZDGvaAn29gghOkj04SkEWViZR3dU3DGrA+5ZX+zr6kZduus3Hf0bVHT
I318PZGTml1wm6faDRomE8bI5xADWhPiCQ1Gf7cFPiqaPkq7mgdC6SGlQtRAfoP8
ISUJlih0UtsqBWGql4lpk5G6YmvAezguWmMR0/O5Cx5w8YKfXkwAhegGmMGIoJFO
oSzJrS7jK2GnGCuRG65OQVC5HiQY2fFF0JePLWG/D56djNxMbPNGTHF3+yBWg0DU
0xJKYKGFdjFcw0Wi0m2j49Pv3JD1f78c2Z3I/65pkklZGu4awnKQcHeGIbdYF0hQ
LtDSBV4DR9q5GVxSR9JPgQ==
-----END CERTIFICATE-----""" ,
                  "STM2": """-----BEGIN CERTIFICATE-----
MIIDzDCCArSgAwIBAgIEAAAAAzANBgkqhkiG9w0BAQsFADBKMQswCQYDVQQGEwJD
SDEeMBwGA1UEChMVU1RNaWNyb2VsZWN0cm9uaWNzIE5WMRswGQYDVQQDExJTVE0g
VFBNIEVLIFJvb3QgQ0EwHhcNMTEwMTIxMDAwMDAwWhcNMjkxMjMxMDAwMDAwWjBV
MQswCQYDVQQGEwJDSDEeMBwGA1UEChMVU1RNaWNyb2VsZWN0cm9uaWNzIE5WMSYw
JAYDVQQDEx1TVE0gVFBNIEVLIEludGVybWVkaWF0ZSBDQSAwMjCCASIwDQYJKoZI
hvcNAQEBBQADggEPADCCAQoCggEBAJO3ihn/uHgV3HrlPZpv8+1+xg9ccLf3pVXJ
oT5n8PHHixN6ZRBmf/Ng85/ODZzxnotC64WD8GHMLyQ0Cna3MJF+MGJZ5R5JkuJR
B4CtgTPwcTVZIsCuup0aDWnPzYqHwvfaiD2FD0aaxCnTKIjWU9OztTD2I61xW2LK
EY4Vde+W3C7WZgS5TpqkbhJzy2NJj6oSMDKklfI3X8jVf7bngMcCR3X3NcIo349I
Dt1r1GfwB+oWrhogZVnMFJKAoSYP8aQrLDVl7SQOAgTXz2IDD6bo1jga/8Kb72dD
h8D2qrkqWh7Hwdas3jqqbb9uiq6O2dJJY86FjffjXPo3jGlFjTsCAwEAAaOBrjCB
qzAdBgNVHQ4EFgQUVx+Aa0fM55v6NZR87Yi40QBa4J4wHwYDVR0jBBgwFoAUb+bF
bAe3bIsKgZKDXMtBHvaO0ScwRQYDVR0gAQH/BDswOTA3BgRVHSAAMC8wLQYIKwYB
BQUHAgEWIWh0dHA6Ly93d3cuc3QuY29tL1RQTS9yZXBvc2l0b3J5LzAOBgNVHQ8B
Af8EBAMCAAQwEgYDVR0TAQH/BAgwBgEB/wIBATANBgkqhkiG9w0BAQsFAAOCAQEA
4gllWq44PFWcv0JgMPOtyXDQx30YB5vBpjS0in7f/Y/r+1Dd8q3EZwNOwYApe+Lp
/ldNqCXw4XzmO8ZCVWOdQdVOqHZuSOhe++Jn0S7M4z2/1PQ6EbRczGfw3dlX63Ec
cEnrn6YMcgPC63Q+ID53vbTS3gpeX/SGpngtVwnzpuJ5rBajqSQUo5jBTBtuGQpO
Ko6Eu7U6Ouz7BVgOSn0mLbfSRb77PjOLZ3+97gSiMmV0iofS7ufemYqA8sF7ZFv/
lM2eOe/eeS56Jw+IPsnEU0Tf8Tn9hnEig1KP8VByRTWAJgiEOgX2nTs5iJbyZeIZ
RUjDHQQ5onqhgjpfRsC95g==
-----END CERTIFICATE-----""",
                  "NTC1": """-----BEGIN CERTIFICATE-----
MIIDSjCCAjKgAwIBAgIGAK3jXfbVMA0GCSqGSIb3DQEBBQUAMFIxUDAcBgNVBAMT
FU5UQyBUUE0gRUsgUm9vdCBDQSAwMTAlBgNVBAoTHk51dm90b24gVGVjaG5vbG9n
eSBDb3Jwb3JhdGlvbjAJBgNVBAYTAlRXMB4XDTEyMDcxMTE2MjkzMFoXDTMyMDcx
MTE2MjkzMFowUjFQMBwGA1UEAxMVTlRDIFRQTSBFSyBSb290IENBIDAxMCUGA1UE
ChMeTnV2b3RvbiBUZWNobm9sb2d5IENvcnBvcmF0aW9uMAkGA1UEBhMCVFcwggEi
MA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQDoNqxhtD4yUtXhqKQGGZemoKJy
uj1RnWvmNgzItLeejNU8B6fOnpMQyoS4K72tMhhFRK2jV9RYzyJMSjEwyX0ASTO1
2yMti2UJQS60d36eGwk8WLgrFnnITlemshi01h9t1MOmay3TO1LLH/3/VDKJ+jbd
cbfIO2bBquN8r3/ojYUaNSPj6pK1mmsMoJXF4dGRSEwb/4ozBIw5dugm1MEq4Zj3
GZ0YPg5wyLRugQbt7DkUOX4FGuK5p/C0u5zX8u33EGTrDrRz3ye3zO+aAY1xXF/m
qwEqgxX5M8f0/DXTTO/CfeIksuPeOzujFtXfi5Cy64eeIZ0nAUG3jbtnGjoFAgMB
AAGjJjAkMA4GA1UdDwEB/wQEAwICBDASBgNVHRMBAf8ECDAGAQH/AgEAMA0GCSqG
SIb3DQEBBQUAA4IBAQBBQznOPJAsD4Yvyt/hXtVJSgBX/+rRfoaqbdt3UMbUPJYi
pUoTUgaTx02DVRwommO+hLx7CS++1F2zorWC8qQyvNbg7iffQbbjWitt8NPE6kCr
q0Y5g7M/LkQDd5N3cFfC15uFJOtlj+A2DGzir8dlXU/0qNq9dBFbi+y+Y3rAT+wK
fktmN82UT861wTUzDvnXO+v7H5DYXjUU8kejPW6q+GgsccIbVTOdHNNWbMrcD9yf
oS91nMZ/+/n7IfFWXNN82qERsrvOFCDsbIzUOR30N0IP++oqGfwAbKFfCOCFUz6j
jpXUdJlh22tp12UMsreibmi5bsWYBgybwSbRgvzE
-----END CERTIFICATE-----""",
                  "NTC2": """-----BEGIN CERTIFICATE-----
MIIDSjCCAjKgAwIBAgIGAPadBmPZMA0GCSqGSIb3DQEBBQUAMFIxUDAcBgNVBAMT
FU5UQyBUUE0gRUsgUm9vdCBDQSAwMjAlBgNVBAoTHk51dm90b24gVGVjaG5vbG9n
eSBDb3Jwb3JhdGlvbjAJBgNVBAYTAlRXMB4XDTEyMDcxMTE2MzMyNFoXDTMyMDcx
MTE2MzMyNFowUjFQMBwGA1UEAxMVTlRDIFRQTSBFSyBSb290IENBIDAyMCUGA1UE
ChMeTnV2b3RvbiBUZWNobm9sb2d5IENvcnBvcmF0aW9uMAkGA1UEBhMCVFcwggEi
MA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQDSagWxaANT1YA2YUSN7sq7yzOT
1ymbIM+WijhE5AGcLwLFoJ9fmaQrYL6fAW2EW/Q3yu97Q9Ysr8yYZ2XCCfxfseEr
Vs80an8Nk6LkTDz8+0Hm0Cct0klvNUAZEIvWpmgHZMvGijXyOcp4z494d8B28Ynb
I7x0JMXZZQQKQi+WfuHtntF+2osYScweocipPrGeONLKU9sngWZ2vnnvw1SBneTa
irxq0Q0SD6Bx9jtxvdf87euk8JzfPhX8jp8GEeAjmLwGR+tnOQrDmczGNmp7YYNN
R+Q7NZVoYWHw5jaoZnNxbouWUXZZxFqDsB/ndCKWtsIzRYPuWcqrFcmUN4SVAgMB
AAGjJjAkMA4GA1UdDwEB/wQEAwICBDASBgNVHRMBAf8ECDAGAQH/AgEAMA0GCSqG
SIb3DQEBBQUAA4IBAQAIkdDSErzPLPYrVthw4lKjW4tRYelUicMPEHKjQeVUAAS5
y9XTzB4DWISDAFsgtQjqHJj0xCG+vpY0Rmn2FCO/0YpP+YBQkdbJOsiyXCdFy9e4
gGjQ24gw1B+rr84+pkI51y952NYBdoQDeb7diPe+24U94f//DYt/JQ8cJua4alr3
2Pohhh5TxCXXfU2EHt67KyqBSxCSy9m4OkCOGLHL2X5nQIdXVj178mw6DSAwyhwR
n3uJo5MvUEoQTFZJKGSXfab619mIgzEr+YHsIQToqf44VfDMDdM+MFiXQ3a5fLii
hEKQ9DhBPtpHAbhFA4jhCiG9HA8FdEplJ+M4uxNz
-----END CERTIFICATE-----""",
                  "IFX1": """-----BEGIN CERTIFICATE-----
MIIEnzCCA4egAwIBAgIEMV64bDANBgkqhkiG9w0BAQUFADBtMQswCQYDVQQGEwJE
RTEQMA4GA1UECBMHQmF2YXJpYTEhMB8GA1UEChMYSW5maW5lb24gVGVjaG5vbG9n
aWVzIEFHMQwwCgYDVQQLEwNBSU0xGzAZBgNVBAMTEklGWCBUUE0gRUsgUm9vdCBD
QTAeFw0wNTEwMjAxMzQ3NDNaFw0yNTEwMjAxMzQ3NDNaMHcxCzAJBgNVBAYTAkRF
MQ8wDQYDVQQIEwZTYXhvbnkxITAfBgNVBAoTGEluZmluZW9uIFRlY2hub2xvZ2ll
cyBBRzEMMAoGA1UECxMDQUlNMSYwJAYDVQQDEx1JRlggVFBNIEVLIEludGVybWVk
aWF0ZSBDQSAwMTCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBALftPhYN
t4rE+JnU/XOPICbOBLvfo6iA7nuq7zf4DzsAWBdsZEdFJQfaK331ihG3IpQnlQ2i
YtDim289265f0J4OkPFpKeFU27CsfozVaNUm6UR/uzwA8ncxFc3iZLRMRNLru/Al
VG053ULVDQMVx2iwwbBSAYO9pGiGbk1iMmuZaSErMdb9v0KRUyZM7yABiyDlM3cz
UQX5vLWV0uWqxdGoHwNva5u3ynP9UxPTZWHZOHE6+14rMzpobs6Ww2RR8BgF96rh
4rRAZEl8BXhwiQq4STvUXkfvdpWH4lzsGcDDtrB6Nt3KvVNvsKz+b07Dk+Xzt+EH
NTf3Byk2HlvX+scCAwEAAaOCATswggE3MB0GA1UdDgQWBBQ4k8292HPEIzMV4bE7
qWoNI8wQxzAOBgNVHQ8BAf8EBAMCAgQwEgYDVR0TAQH/BAgwBgEB/wIBADBYBgNV
HSABAf8ETjBMMEoGC2CGSAGG+EUBBy8BMDswOQYIKwYBBQUHAgEWLWh0dHA6Ly93
d3cudmVyaXNpZ24uY29tL3JlcG9zaXRvcnkvaW5kZXguaHRtbDCBlwYDVR0jBIGP
MIGMgBRW65FEhWPWcrOu1EWWC/eUDlRCpqFxpG8wbTELMAkGA1UEBhMCREUxEDAO
BgNVBAgTB0JhdmFyaWExITAfBgNVBAoTGEluZmluZW9uIFRlY2hub2xvZ2llcyBB
RzEMMAoGA1UECxMDQUlNMRswGQYDVQQDExJJRlggVFBNIEVLIFJvb3QgQ0GCAQMw
DQYJKoZIhvcNAQEFBQADggEBABJ1+Ap3rNlxZ0FW0aIgdzktbNHlvXWNxFdYIBbM
OKjmbOos0Y4O60eKPu259XmMItCUmtbzF3oKYXq6ybARUT2Lm+JsseMF5VgikSlU
BJALqpKVjwAds81OtmnIQe2LSu4xcTSavpsL4f52cUAu/maMhtSgN9mq5roYptq9
DnSSDZrX4uYiMPl//rBaNDBflhJ727j8xo9CCohF3yQUoQm7coUgbRMzyO64yMIO
3fhb+Vuc7sNwrMOz3VJN14C3JMoGgXy0c57IP/kD5zGRvljKEvrRC2I147+fPeLS
DueRMS6lblvRKiZgmGAg7YaKOkOaEmVDMQ+fTo2Po7hI5wc=
-----END CERTIFICATE-----""",
                  "IFX2": """-----BEGIN CERTIFICATE-----
MIIEnzCCA4egAwIBAgIEaItIgTANBgkqhkiG9w0BAQUFADBtMQswCQYDVQQGEwJE
RTEQMA4GA1UECBMHQmF2YXJpYTEhMB8GA1UEChMYSW5maW5lb24gVGVjaG5vbG9n
aWVzIEFHMQwwCgYDVQQLEwNBSU0xGzAZBgNVBAMTEklGWCBUUE0gRUsgUm9vdCBD
QTAeFw0wNjEyMjExMDM0MDBaFw0yNjEyMjExMDM0MDBaMHcxCzAJBgNVBAYTAkRF
MQ8wDQYDVQQIEwZTYXhvbnkxITAfBgNVBAoTGEluZmluZW9uIFRlY2hub2xvZ2ll
cyBBRzEMMAoGA1UECxMDQUlNMSYwJAYDVQQDEx1JRlggVFBNIEVLIEludGVybWVk
aWF0ZSBDQSAwMjCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBAK6KnP5R
8ppq9TtPu3mAs3AFxdWhzK5ks+BixGR6mpzyXG64Bjl4xzBXeBIVtlBZXYvIAJ5s
eCTEEsnZc9eKNJeFLdmXQ/siRrTeonyxoS4aL1mVEQebLUz2gN9J6j1ewly+OvGk
jEYouGCzA+fARzLeRIrhuhBI0kUChbH7VM8FngJsbT4xKB3EJ6Wttma25VSimkAr
SPS6dzUDRS1OFCWtAtHJW6YjBnA4wgR8WfpXsnjeNpwEEB+JciWu1VAueLNI+Kis
RiferCfsgWRvHkR6RQf04h+FlhnYHJnf1ktqcEi1oYAjLsbYOAwqyoU1Pev9cS28
EA6FTJcxjuHhH9ECAwEAAaOCATswggE3MB0GA1UdDgQWBBRDMlr1UAQGVIkwzamm
fceAZ7l4ATAOBgNVHQ8BAf8EBAMCAgQwEgYDVR0TAQH/BAgwBgEB/wIBADBYBgNV
HSABAf8ETjBMMEoGC2CGSAGG+EUBBy8BMDswOQYIKwYBBQUHAgEWLWh0dHA6Ly93
d3cudmVyaXNpZ24uY29tL3JlcG9zaXRvcnkvaW5kZXguaHRtbDCBlwYDVR0jBIGP
MIGMgBRW65FEhWPWcrOu1EWWC/eUDlRCpqFxpG8wbTELMAkGA1UEBhMCREUxEDAO
BgNVBAgTB0JhdmFyaWExITAfBgNVBAoTGEluZmluZW9uIFRlY2hub2xvZ2llcyBB
RzEMMAoGA1UECxMDQUlNMRswGQYDVQQDExJJRlggVFBNIEVLIFJvb3QgQ0GCAQMw
DQYJKoZIhvcNAQEFBQADggEBAIZAaYGzf9AYv6DqoUNx6wdpayhCeX75/IHuFQ/d
gLzat9Vd6qNKdAByskpOjpE0KRauEzD/BhTtkEJDazPSmVP1QxAPjqGaD+JjqhS/
Q6aY+1PSDi2zRIDA66V2yFJDcUBTtShbdTg144YSkVSY5UCKhQrsdg8yAbs7saAB
LHzVebTXffjmkTk5GZk26d/AZQRjfssta1N/TWhWTfuZtwYvjZmgDPeCfr6AOPLr
pVJz+ntzUKGpQ+5mwDJXMZ0qeiFIgXUlU0D+lfuajc/x9rgix9cM+o7amgDlRi1T
55Uu2vzUQ9jLUaISFaTTMag+quBDhx8BDVu+igLp5hvBtxQ=
-----END CERTIFICATE-----""",
                  "IFX3": """-----BEGIN CERTIFICATE-----
MIIEnzCCA4egAwIBAgIEH7fYljANBgkqhkiG9w0BAQUFADBtMQswCQYDVQQGEwJE
RTEQMA4GA1UECBMHQmF2YXJpYTEhMB8GA1UEChMYSW5maW5lb24gVGVjaG5vbG9n
aWVzIEFHMQwwCgYDVQQLEwNBSU0xGzAZBgNVBAMTEklGWCBUUE0gRUsgUm9vdCBD
QTAeFw0wNzA0MTMxNjQ0MjRaFw0yNzA0MTMxNjQ0MjRaMHcxCzAJBgNVBAYTAkRF
MQ8wDQYDVQQIEwZTYXhvbnkxITAfBgNVBAoTGEluZmluZW9uIFRlY2hub2xvZ2ll
cyBBRzEMMAoGA1UECxMDQUlNMSYwJAYDVQQDEx1JRlggVFBNIEVLIEludGVybWVk
aWF0ZSBDQSAwMzCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBAJWdPAuH
z/p1tIwB1QXlPD/PjedZ4uBZdwPH5tI3Uve0TzbR/mO5clx/loWn7nZ5cHkH1nhB
R67JEFY0a9GithPfITh0XRxPcisLBE/SoqZ90KHFaS+N6SwOpdCP0GlUg1OesKCF
79Z6fXrkTZsVpPqdawdZK+oUsDO9z9U6xqV7bwsS75Y+QiHsm6UTgAkSNQnuFMP3
NqQyDi/BaWaYRGQ6K8pM7Y7e1h21z/+5X7LncZXU8hgpYpu2zQPg96IkYboVUKL4
00snaPcOvfagsBUGlBltNfz7geaSuWTCdwEiwlkCYZqCtbkAj5FiStajrzP72BfT
2fshIv+5eF7Qp5ECAwEAAaOCATswggE3MB0GA1UdDgQWBBTGyypNtylL6RFyT1BB
MQtMQvibsjAOBgNVHQ8BAf8EBAMCAgQwEgYDVR0TAQH/BAgwBgEB/wIBADBYBgNV
HSABAf8ETjBMMEoGC2CGSAGG+EUBBy8BMDswOQYIKwYBBQUHAgEWLWh0dHA6Ly93
d3cudmVyaXNpZ24uY29tL3JlcG9zaXRvcnkvaW5kZXguaHRtbDCBlwYDVR0jBIGP
MIGMgBRW65FEhWPWcrOu1EWWC/eUDlRCpqFxpG8wbTELMAkGA1UEBhMCREUxEDAO
BgNVBAgTB0JhdmFyaWExITAfBgNVBAoTGEluZmluZW9uIFRlY2hub2xvZ2llcyBB
RzEMMAoGA1UECxMDQUlNMRswGQYDVQQDExJJRlggVFBNIEVLIFJvb3QgQ0GCAQMw
DQYJKoZIhvcNAQEFBQADggEBAGN1bkh4J90DGcOPP2BlwE6ejJ0iDKf1zF+7CLu5
WS5K4dvuzsWUoQ5eplUt1LrIlorLr46mLokZD0RTG8t49Rcw4AvxMgWk7oYk69q2
0MGwXwgZ5OQypHaPwslmddLcX+RyEvjrdGpQx3E/87ZrQP8OKnmqI3pBlB8QwCGL
SV9AERaGDpzIHoObLlUjgHuD6aFekPfeIu1xbN25oZCWmqFVIhkKxWE1Xu+qqHIA
dnCFhoIWH3ie9OsJh/iDRaANYYGyplIibDx1FJA8fqiBiBBKUlPoJvbqmZs4meMd
OoeOuCvQ7op28UtaoV6H6BSYmN5dOgW7r1lX2Re0nd84NGE=
-----END CERTIFICATE-----""",
                  "IFX4": """-----BEGIN CERTIFICATE-----
MIIEnzCCA4egAwIBAgIEDhD4wDANBgkqhkiG9w0BAQUFADBtMQswCQYDVQQGEwJE
RTEQMA4GA1UECBMHQmF2YXJpYTEhMB8GA1UEChMYSW5maW5lb24gVGVjaG5vbG9n
aWVzIEFHMQwwCgYDVQQLEwNBSU0xGzAZBgNVBAMTEklGWCBUUE0gRUsgUm9vdCBD
QTAeFw0wNzEyMDMxMzA3NTVaFw0yNzEyMDMxMzA3NTVaMHcxCzAJBgNVBAYTAkRF
MQ8wDQYDVQQIEwZTYXhvbnkxITAfBgNVBAoTGEluZmluZW9uIFRlY2hub2xvZ2ll
cyBBRzEMMAoGA1UECxMDQUlNMSYwJAYDVQQDEx1JRlggVFBNIEVLIEludGVybWVk
aWF0ZSBDQSAwNDCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBAN3UBmDk
jJzzJ+WCgrq4tILtE9KJPMGHwvCsbJOlo7eHiEb8JQzGK1prkPQ3dowFRXPnqONP
WUa36/J3R32xgvuZHqAdliZCt8IUb9qYhDenuXo1SSqJ8LWp30QIJ0vnkaQ2TCkO
bveZZR3hK2OZKRTkFaV/iy2RH+Qs4JAe3diD8mlIu2gXAXnKJSkrzW6gbMzrlTOi
RCuGcatpy7Hfmodbz/0Trbuwtc3dyJZ3Ko1z9bz2Oirjh93RrmYjbtL0HhkAjMOR
83GLrzwUddSqmxtXXX8j5i+/gmE3AO71swOIESdGugxaKUzJ1jTqWKMZcx0E6BFI
lDIfKk0fJlSxHfECAwEAAaOCATswggE3MB0GA1UdDgQWBBSIs8E/YQXRBCKfWsDr
SZVkrNRzvTAOBgNVHQ8BAf8EBAMCAgQwEgYDVR0TAQH/BAgwBgEB/wIBADBYBgNV
HSABAf8ETjBMMEoGC2CGSAGG+EUBBy8BMDswOQYIKwYBBQUHAgEWLWh0dHA6Ly93
d3cudmVyaXNpZ24uY29tL3JlcG9zaXRvcnkvaW5kZXguaHRtbDCBlwYDVR0jBIGP
MIGMgBRW65FEhWPWcrOu1EWWC/eUDlRCpqFxpG8wbTELMAkGA1UEBhMCREUxEDAO
BgNVBAgTB0JhdmFyaWExITAfBgNVBAoTGEluZmluZW9uIFRlY2hub2xvZ2llcyBB
RzEMMAoGA1UECxMDQUlNMRswGQYDVQQDExJJRlggVFBNIEVLIFJvb3QgQ0GCAQMw
DQYJKoZIhvcNAQEFBQADggEBAFtqClQNBLOzcGZUpsBqlz3frzM45iiBpxosG1Re
IgoAgtIBEtl609TG51tmpm294KqpfKZVO+xNzovm8k/heGb0jmYf+q1ggrk2qT4v
Qy2jgE0jbP/P8WWq8NHC13uMcBUGPaka7yofEDDwz7TcduQyJVfG2pd1vflnzP0+
iiJpfCk3CAQQnb+B7zsOp7jHNwpvHP+FhNwZaikaa0OdR/ML9da1sOOW3oJSTEjW
SMLuhaZHtcVgitvtOVvCI/aq47rNJku3xQ7c/s8FHnFzQQ+Q4TExbP20SrqQIlL/
9sFAb7/nKYNauusakiF3pfvMrJOJigNfJyIcWaGfyyQtVVI=
-----END CERTIFICATE-----""",
                  "IFX5": """-----BEGIN CERTIFICATE-----
MIIEnzCCA4egAwIBAgIEVuRoqzANBgkqhkiG9w0BAQUFADBtMQswCQYDVQQGEwJE
RTEQMA4GA1UECBMHQmF2YXJpYTEhMB8GA1UEChMYSW5maW5lb24gVGVjaG5vbG9n
aWVzIEFHMQwwCgYDVQQLEwNBSU0xGzAZBgNVBAMTEklGWCBUUE0gRUsgUm9vdCBD
QTAeFw0wOTEyMTExMDM4NDJaFw0yOTEyMTExMDM4NDJaMHcxCzAJBgNVBAYTAkRF
MQ8wDQYDVQQIEwZTYXhvbnkxITAfBgNVBAoTGEluZmluZW9uIFRlY2hub2xvZ2ll
cyBBRzEMMAoGA1UECxMDQUlNMSYwJAYDVQQDEx1JRlggVFBNIEVLIEludGVybWVk
aWF0ZSBDQSAwNTCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBAL79zMCO
bjkg7gCWEuyGO49CisF/QrGoz9adW1FBuSW8U9IOlvWXNsvoasC1mhrsfkRRojuU
mWifxxxcVfOI9v1SbRfJ+i6lG21IcVe6ywLJdDliT+3vzvrb/2hU/XjCCMDWb/Pw
aZslV5iL4QEiKxvRIiWMYHW0MkkL7mzRBDVN/Vz3ZiL5Lpq7awiKuX9OXpS2a1wf
qSGAlm2TxjU884q9Ky85JJugn0Q/C3dc8aaFPKLHlRs6rIvN1l0LwB1b5EWPzTPJ
d9EhRPFJOAbJS66nSgX06Fl7eWB71ow6w/25otLQCbpy6OrF8wBVMtPMHqFb1c32
PaaNzpCBnIU7vaMCAwEAAaOCATswggE3MB0GA1UdDgQWBBS7z3zBhCExZtq1vlOo
cBTd00jYzDAOBgNVHQ8BAf8EBAMCAgQwEgYDVR0TAQH/BAgwBgEB/wIBADBYBgNV
HSABAf8ETjBMMEoGC2CGSAGG+EUBBy8BMDswOQYIKwYBBQUHAgEWLWh0dHA6Ly93
d3cudmVyaXNpZ24uY29tL3JlcG9zaXRvcnkvaW5kZXguaHRtbDCBlwYDVR0jBIGP
MIGMgBRW65FEhWPWcrOu1EWWC/eUDlRCpqFxpG8wbTELMAkGA1UEBhMCREUxEDAO
BgNVBAgTB0JhdmFyaWExITAfBgNVBAoTGEluZmluZW9uIFRlY2hub2xvZ2llcyBB
RzEMMAoGA1UECxMDQUlNMRswGQYDVQQDExJJRlggVFBNIEVLIFJvb3QgQ0GCAQMw
DQYJKoZIhvcNAQEFBQADggEBAHomNJtmFNtRJI2+s6ZwdzCTHXXIcR/T+N/lfPbE
hIUG4Kg+3uQMP7zBi22m3I3Kk9SXsjLqV5mnsQUGMGlF7jw5W5Q+d6NSJz4taw9D
2DsiUxE/i5vrjWiUaWxv2Eckd4MUexe5Qz8YSh4FPqLB8FZnAlgx2kfdzRIUjkMq
EgFK8ZRSUjXdczvsud68YPVMIZTxK0L8POGJ6RYiDrjTelprfZ4pKKZ79XwxwAIo
pG6emUEf+doRT0KoHoCHr9vvWCWKhojqlQ6jflPZcEsNBMbq5KHVN77vOU58OKx1
56v3EaqrZenVFt8+n6h2NzhOmg2quQXIr0V9jEg8GAMehDs=
-----END CERTIFICATE-----""",
                  "IFX8": """-----BEGIN CERTIFICATE-----
MIIEnzCCA4egAwIBAgIEfGoY6jANBgkqhkiG9w0BAQUFADBtMQswCQYDVQQGEwJE
RTEQMA4GA1UECBMHQmF2YXJpYTEhMB8GA1UEChMYSW5maW5lb24gVGVjaG5vbG9n
aWVzIEFHMQwwCgYDVQQLEwNBSU0xGzAZBgNVBAMTEklGWCBUUE0gRUsgUm9vdCBD
QTAeFw0xMjA3MTcwOTI0NTJaFw0zMDEwMTgyMzU5NTlaMHcxCzAJBgNVBAYTAkRF
MQ8wDQYDVQQIEwZTYXhvbnkxITAfBgNVBAoTGEluZmluZW9uIFRlY2hub2xvZ2ll
cyBBRzEMMAoGA1UECxMDQUlNMSYwJAYDVQQDEx1JRlggVFBNIEVLIEludGVybWVk
aWF0ZSBDQSAwODCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBAOJaIJu6
r/betrMgWJ/JZ5j8ytoAA9RWq0cw7+W0e5L2kDLJMM288wYT+iEbfwx6sWSLAl7q
okXYDtTB9MFNhQ5ZWFLslFXbYigtXJxwANcSdPISTF1Czn6LLi1fu1EHddwCXFC8
xaX0iGgQ9pZklvAy2ijK9BPHquWisisEiWZNRT9dCVylzOR3+p2YOC3ZrRmg7Bj+
DkC7dltTTO6dPR+LNOFe01pJlpZdF4YHcu4EC10gRu0quZz1LtDZWFKezK7rg5Rj
LSAJbKOsGXjl6hQXMtADEX9Vlz1vItD21OYCNRsu6VdipiL0bl0aAio4BV3GMyjk
0gHnQwCk9k/YPU8CAwEAAaOCATswggE3MB0GA1UdDgQWBBRMS01kiQjkW/5aENNj
h6aIrsHPeDAOBgNVHQ8BAf8EBAMCAgQwEgYDVR0TAQH/BAgwBgEB/wIBADBYBgNV
HSABAf8ETjBMMEoGC2CGSAGG+EUBBy8BMDswOQYIKwYBBQUHAgEWLWh0dHA6Ly93
d3cudmVyaXNpZ24uY29tL3JlcG9zaXRvcnkvaW5kZXguaHRtbDCBlwYDVR0jBIGP
MIGMgBRW65FEhWPWcrOu1EWWC/eUDlRCpqFxpG8wbTELMAkGA1UEBhMCREUxEDAO
BgNVBAgTB0JhdmFyaWExITAfBgNVBAoTGEluZmluZW9uIFRlY2hub2xvZ2llcyBB
RzEMMAoGA1UECxMDQUlNMRswGQYDVQQDExJJRlggVFBNIEVLIFJvb3QgQ0GCAQMw
DQYJKoZIhvcNAQEFBQADggEBALMiDyQ9WKH/eTI84Mk8KYk+TXXEwf+fhgeCvxOQ
G0FTSmOpJaNIzxWXr/gDbY3dO0ODjWRKYvhimZUuV+ckMA+wZX2C6o8g5njpWIOH
pSAa+W35ijArh0Zt3MASJ46avd+fnQGTdzT0hK46gx6n2KixLvaZsR3JtuwUFYlQ
wzmz/UsbBNEoPiR8p5E0Zf5GEGiTqkmBVYyS6XA34axpMMRHy0wI7AGs0gVihwUM
rr0iWOu+GAcrm11lcYzqJvuEkfenAF62ufA2Ktv+Ut2xiRC0jUIp73CeplAJsqBr
camV3pJn3qYPI5c1njMRYnoRFWQbrOR5ADWDQLFQPYRrJmg=
-----END CERTIFICATE-----""",
                  "IFX15": """-----BEGIN CERTIFICATE-----
MIIEnzCCA4egAwIBAgIER3V5aDANBgkqhkiG9w0BAQUFADBtMQswCQYDVQQGEwJE
RTEQMA4GA1UECBMHQmF2YXJpYTEhMB8GA1UEChMYSW5maW5lb24gVGVjaG5vbG9n
aWVzIEFHMQwwCgYDVQQLEwNBSU0xGzAZBgNVBAMTEklGWCBUUE0gRUsgUm9vdCBD
QTAeFw0xMjExMTQxNDQzMzRaFw0zMDEwMTgyMzU5NTlaMHcxCzAJBgNVBAYTAkRF
MQ8wDQYDVQQIEwZTYXhvbnkxITAfBgNVBAoTGEluZmluZW9uIFRlY2hub2xvZ2ll
cyBBRzEMMAoGA1UECxMDQUlNMSYwJAYDVQQDEx1JRlggVFBNIEVLIEludGVybWVk
aWF0ZSBDQSAxNTCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBAKS6pgcg
OQWSozVbMkdf9jZkpGdT4U735zs0skfpjoKK2CgpLMO/+oGKbObm/DQPRQO/oxvq
jJNBKz55QBgKd+MoQ6t+2J8mcQ91Nfwqnm1C4r+c4zezJ1Utk/KIYNqpFDAzefBA
/lK8IxQ6kmzxcIFE4skaFsSgkearSZGG6sA9A51yxwvs8yUrQF51ICEUM7wDb4cM
53utaFdm6p6m9UZGSmmrdTiemOkuuwtl8IUQXfuk9lFyQsACBTM95Hrts0IzI6hX
QeTwSL4JqyEnKP9vbtT4eXzWNycqSYBf0+Uo/HHZo9WuVDUaA4I9zcmD0qCvSOT0
NAj4ifJ7SPGInU0CAwEAAaOCATswggE3MB0GA1UdDgQWBBR4pAnEV95pJvbfQsYR
TrflaptW5zAOBgNVHQ8BAf8EBAMCAgQwEgYDVR0TAQH/BAgwBgEB/wIBADBYBgNV
HSABAf8ETjBMMEoGC2CGSAGG+EUBBy8BMDswOQYIKwYBBQUHAgEWLWh0dHA6Ly93
d3cudmVyaXNpZ24uY29tL3JlcG9zaXRvcnkvaW5kZXguaHRtbDCBlwYDVR0jBIGP
MIGMgBRW65FEhWPWcrOu1EWWC/eUDlRCpqFxpG8wbTELMAkGA1UEBhMCREUxEDAO
BgNVBAgTB0JhdmFyaWExITAfBgNVBAoTGEluZmluZW9uIFRlY2hub2xvZ2llcyBB
RzEMMAoGA1UECxMDQUlNMRswGQYDVQQDExJJRlggVFBNIEVLIFJvb3QgQ0GCAQMw
DQYJKoZIhvcNAQEFBQADggEBAAnZDdJZs5QgAXnl0Jo5sCqktZcwcK+V1+uhsqrT
Z7OJ9Ze1YJ9XB14KxRfmck7Erl5HVc6PtUcLnR0tuJKKKqm7dTe4sQEFYd5usjrW
KSG6y7BOH7AdonocILY9OIxuNwxMAqhK8LIjkkRCeOWSvCqLnaLtrP52C0fBkTTM
SWX7YnsutXEpwhro3Qsnm9hL9s3s/WoIuNKUcLFH/qWKztpxXnF0zip73gcZbwEy
1GPQQpYnxFJ2R2ab2RHlO+3Uf3FDxn+eRLXNl95ZZ6GE4OIIpKEg2urIiig0HmGA
ijO6JfJxT30H9QNsx78sjYs7pOfMw6DfiqJ8Fx82GcCUOyM=
-----END CERTIFICATE-----""" }


trusted_keys = {"ATM1": {"key": "E5AFB8C97B6E6D49C624FCFB6558D6B291A17B94EBF4186B590F5039F0E85659268BEB60D86A9CF6A03D477F5686288498AB90DFEE1722F3BE5C516B542BFEF18B849C1208BB8E85117D4B046ECB9D425B920015D29CC73163A084B84320670683FEA43BD7C7FBB29CC1FC0D6A1F992E47DB7E2B37726D3D465386F114AAF0BC8AF19734ED01F633B2FFF0F1674514393270205BBBEE93C87F33AD934F2FB20D5B9697F8E7877BEB2A054CA0EC8BFE233711D147215FABFE524E23F1D1025922782446889D64248E2D42951788BFAD2B6881D720319EA712433596C6536EBBAB00515DAD23EA8C54CDA8E9E4F57FF30CEFE6F89E6CAE06B74E20EE5DBD37A4EF",
                         "exponent": "10001"},
                "ATM2": {"key": "E9EFE830CCAFECD3E534AA3D03B96CC090E4135E0B6464AC2A2472CF225EDAA1C2A01C2C644AB7415DB0E1DB9C9E070ECAC45A7330DDF0292EF59DF7D9D6E2F53ABA4596A993F78BEE670117F5C136EED67EDDCF0D14F3B3C829337C451E8E7DF8E02379AC774C4F3247A3E18A2A69E36B88F5FD7CE2F42C830CC458DCFA90C50FE66C1EDC79BDCBC4654F3AE9240B55B56F70ECB9A849E3871E0CEC1061BDAB91763E463A5F416DF5E0D06883A54E87E4487CEF1B654BBFC30920D3239D7ACF9EF17C76A1B7F25CC022F0DF24A2B11393236366A815CD5D7C84900EFE2C631D366FA8F07C397CA450ABC02CC7EDC5A6204D210F6055D8BA6EAD44538BE92431",
                         "exponent": "10001"},
                "ATM3": {"key": "98501401327FF3121EB855B468A3597300AD0CB0CE4281887B3FAC83AE04989FAB10A3477CF423EDE7B7531880456A0BBE6ACCC0C6451D756E1DBE90E905011F63A65197E17015E6F7865B5EB150C83C68B11DE553E259BB924AD17EFA919010B62048DBF52424CB74C51526D4FEE92272A7AA4F47630D87A70AC2619208EFC47637C6DF1890173A9CF5A0EA48EE35477B0B4963F82E9F58E05EE3B0356FB5A2E0DA52B07FF2DF66D25BECA1EA9DBAAD0D86F97800BEA4C55169E2C497DE016E48E45C6C53F886EED4309CBA839F5D6EC829BA56E5B5DDBE1C3AB111AE153CE7B72250B8894B28D3DD6FABE578F53858399D135C58E4D5D35D71316E2B63BC91",
                         "exponent": "10001"},
                "ATM4": {"key": "C6D975B1A96EFF64977AA08632D69CD06302AB1E907A1E0AB6BBE23DF19574E6E4B2EC8644F3EE696DB9FE860D18B95FDB1FE40E592707679914C896F28B4A5D5FB13B9D2E15CC684C75D9D709CC0FCC7A0A0334CF48F70D0E5DD1EBB9B1144377B187604A6EBCC8F4C7CA6091993E0BE531DA15A58FCC448840C7F2AE70C8FE405FDD86929A1400BD1EE2F515EFF70210172C2CEB3C3AAEAB2B39A283CDA4B0388BFD39FFF13B6C4A6500C13FC5CCCFE08BBF71D03D611ED5F22CE14F0C8ACECB7777733E5030E4922C31C68E6A1A0C1174FAB701449082536881B5F20C05EBC93B52015268FF1207AB1D659A7F9A4D34900BEB678079E6962A6E4E697E9B55",
                         "exponent": "10001"},
                "ATM5": {"key": "AA0D458E1390FC6B2A8142FE59205C7D8AF7864C7197510168222A8A895CD51E5399969B687A025082668705DF146845BE166B23401C12A21800D2E0634AE2BE7E21EAF57EAEBC2DC4CD57ED7F21993F8076FC4BDA9F65382A7B5CDA50D91C3EA3FD8986E05252FFA8A56ECAEB03EE9B0529CB880BF9D028CD9C818DA9F90A8F6C3F9621DE4746DFE7B346C7F17F70A74BBE8D8631E094AF4059474CD5CEA6146A933FE7D4F72493A6869BAE70D4CC871E76EE4EB0C65AE4BD4B78B287AEAADB3376FDF79694F513EB210A0EDF1F8149ABBD01BD1DEB5E33A43D13796C23053ED8E6B220D786C8C7B0E203EE241911397C766DA5D496A6026696470E6D249DBD",
                         "exponent": "10001"},
                "ATM6": {"key": "C3DB3DCA4A60CC7D418ABCFC25598773F8D7352685B0341833D85C4B7E75DCFEDAAD2FABFE6BAC994A9F7726D8FC643CF98A8003A219ABEC65199ED65049B1BE8FC79679BF1508F77A96460F7AEE0299BEF1D2D5E07BECE118D9092F1C7E9911672821FA745DAD9DDA0306518D06E1BE5F26009390D91A7D00D699333623ADEEDA764BAA2050DAF379CA827E1790C21FB7E32D84EBDC318999B522FAE20BC0359ECF8ABC81D9C3214BED3200C18AFCEAA6D042C8464F30A8047F977B71455C68404A80F5F064D9BBC63625AF6BDD9C87108BA445FDF827195AF51E1FA529E5AD840F1C3C060C44D0BEACAA320D5A7DAE374C7B8E52B2B20F97132A3BA94A4C45",
                         "exponent": "10001"},
                "ATM7": {"key": "95845F0C3DDB30907BC3A165F8A7B3A08684933CFED9509E17CBF7A21B0D9D228281CC7CBA4ED27B2A79D1B12D2C1EAF3B3C2070CE568C522D2B260B65A1ED3F8DEADE21ECBC84A300635C606710DCDACCE226BAA5CDA0795ADABA995D3D375014E423C1DFB43FF436FD131B598EA0FAC6E3203B48B44735BE17FA6C8DD38A74FE6C6C715DD47D07AA9680B35CFC7DF5C2C04D3769CFBF52B8C04F0C59F015EE170AD8DA08735CC6118F888963ED5D2BB8F339AF4B6971296598BA21C1C02B799ECFD4ECCF174A391A8FB49B843D36C8AC2231ABEEED230071E49658C06E863826F7FCDF3003CA3BDC1E422C5509EB97B2907279FB1E90FBA4E6885B58E4BF6F",
                         "exponent": "10001"},
                "ATM8": {"key": "CA55DA838266CE8A9A4CAF1E09C4A30D238645CAD7F082BF7C16B080458A0203F2FF2BBEF051975CAD745C3788D5F9A501E7C3AFBDF8F429FEBFDFF2F8C7DF5C876E282A91E593FD335F9F064EE4E65E31D92782F4D7C8306F9CD3227A9B59049AC48DD389E52A4F1FA28E782FB0D8F8A9237E1E843F1CB3C6C303AAA4EB3227C14E117692AA392940437418C890E507D5D6CB5868C4814A4AA1C0AED8CE3553B8E68D3A1AB6403E77757E3F2411178FE52644D88AFE89CB5665D6AA4490BBD1D2A2ABCE81E43A28FBCC1A50FF8E81D815B5A4046353B008A7736D7D2E531CBE7D9A95F1A6ECA3EB2DA1D30C4D55190F6699D50346561E0CFD2784DC22000D3F",
                         "exponent": "10001"},
                "ATM9": {"key": "C5AD170489418FDB796D807CD4279A9A5577237AD36AD860C949F654BEFFC27836BCAE71EC10776B5C235EDE64FEEC11FCCE6D7C80CE4A3BA0FD27437D35A46517BCD888FFA1824ECAD72B173133A2E219540EEDFEE29D5F3470CFB759E8B3E7355929F06896503083A5334D9A7BE2799723AA87DA8C371CD040BBDB4353F8DAA690025DD2A60CB3E8B84C0DA89B60B62F1A64ABE61D269DA924E08242AB82C262D707C3B1ADD7635F8416E661F38A0C787DA9C2FC625C5EE4503D7A8BAEE1D9956994A94ED297AC99125B88B476C1AE2E01C43DD0EDE5C7D2C337AD919408BAF794C3D78C6B1FA688194F8CCBAF4EF9408C6DC1EE4E5299EC954EB5737E1707",
                         "exponent": "10001"},
                "ATM10": {"key": "D4711E0A7F36AFC56B83AE21A30BEDB3FD988F9CAE5E112FEC5C146884A8EEB6059C06ECB7231518DB0BDB8ADE456EDA8B28FAE621C4A23C7509AAF7265BBC8587D3AA26A016610AFEA7BC7AB11AB708398C543419D2B76BD4F0EE78586638E97BDF2C4632FF0D0948E4D88A0A53C5E1936A238D7C3069B398F37F40DC519CA240AF92D313C15908C4A19B957D7A07BBDA82E3E157CFBB3DBD7D02C1656240DBE354CBA802A5C51285E8C67E6F434C6064D26DF0AEEAB25EECCACC9E14D17A399D3AA9ED957F24B6D25A74C9C6CEF6859E03D676E2D2968F42070AE4561B2304355AE12937940C7E296C01915BA2442741AFA35F647395EA1AD265115449C64D",
                          "exponent": "10001"},
                "ATM11": {"key": "AAB4B5122D55BCBC5561636FFECDF96989876B930E9EF4326E05BF8B55EE20D66E3D0A98370D36C2B59103979FB76B6CF859090EF6F3E9E76DA87DF40A3C7EA6613D3AFA2D63B3BBADBA2BBB3D96D8FA5C434FE29CB522C4D8AAFC0F2088A45625A4CDB2217A54B3445847B9B1FDEB7BAF82FD94147F0BA9339E9B53426B20CC44829F1208582E42C37072ADADC6DAF5BA3817E0F37A0CE7ADE8172B4E9B18BF12A140F6CBFD37E5FE432A615CEAAB2AC11A0920F3ED854713BA6D54890B0AF2AC0DFB670920265DE4FEA89B4C5CF02557C99C6693E7B2FF4D4549470003B5537EA0915C41A991ECDE9522EA21C7B7E9ED4F2DF27ACA859A48C0AE34E612C4D7",
                          "exponent": "10001"},
                "ATM12": {"key": "D51E1F5416D423BB6C691B92D15BC74E2A2E67B2FF1C0A241C8B28CDE2CA6A68ACB67A0234A332CF8D29C067A72BC9745E7BC9BDEA00953FB7B5B2A699EA3B891D503F6F2C84DF2082739B1D9A4137670F8B24A1D00F2E608117637B0932B359FE1D8C31B8D80F69D4CAB795A6E8FE9B2B526EF981D5EA9C8FDA782416356AAC1706B9B40EAC595C9B1534192327B73D905CB7CDEF3271C4C52B1FF05DEEEF3C782858A03B44BB4CDA2FE9A49750813FC8B9B3AB8594F258FA6F2D00E935FD29FD20E6072C37FD1CE29CF165C54980781CEF4C3C0CEE312C64851018364806189F2B8E552CBAD08834D338BF1E570F43F07D339FC009BBB705F70F686108FA7D",
                          "exponent": "10001"},
                "ATM13": {"key": "C12BD4CD44118C3DCAC99309BB9099B0754BA803749814FCEA78AF8C257E4611EC474B92535D7434A8DBD881D73377D8689960BD945301027773C8CF7346D5B42D3EE76D5028AB7CE8E2E2D3E9EB353D90CCBB6B260C7A791A188AEF6C7B6174BBFCC1F8F1D0D11F2A54E235C70D161552B6C36FA6453DD637851DA74467E8B28F4570AAE7D24F7EE0FB84D0559B0A7DBB38F64CBA7C96331149B0A14637A4BBD1F81BE6F6A9AE307F683D479FC4AAAE5C33062C0F8DF9EDCBA195FA964310FAD49F77AE8D877F9FB7D09AD9176CA8FD35F9A1C750AA7BCB79AA5ED4A6464C3AE290D5C3F5E221479DF24F868100AFD107CB1CB1BC239F9B67A0804ED06004C3",
                          "exponent": "10001"}
}

def integer_ceil(a, b):
    """Return the ceil integer of a div b."""
    quanta, mod = divmod(a, b)
    if mod:
        quanta += 1
    return quanta


def i2osp(x, x_len):
    """
    Converts the integer x to its big-endian representation of length
    x_len.
    """
    if x > 256**x_len:
        raise exceptions.IntegerTooLarge
    h = hex(x)[2:]
    if h[-1] == 'L':
        h = h[:-1]
    if len(h) & 1 == 1:
        h = '0%s' % h
    x = h.decode('hex')
    return '\x00' * int(x_len-len(x)) + x


def mgf1(mgf_seed, mask_len, hash_class=hashlib.sha1):
    """
    Mask Generation Function v1 from the PKCS#1 v2.0 standard.

    :param mgs_seed: the seed, a byte string
    :param mask_len: the length of the mask to generate
    :param hash_class: the digest algorithm to use, default is SHA1

    :returns:: a pseudo-random mask, as a byte string
    """
    h_len = hash_class().digest_size
    if mask_len > 0x10000:
        raise ValueError('mask too long')
    T = ''
    for i in xrange(0, integer_ceil(mask_len, h_len)):
        C = i2osp(i, 4)
        T = T + hash_class(mgf_seed + C).digest()
    return bytearray(T[:mask_len])


def tpm_oaep(plaintext, keylen):
    """Pad plaintext with the TPM-specific varient of OAEP

    :param plaintext: The data that requires padding
    :param keylen: The length of the encryption key
    :returns: a padded plaintext
    """
    m = hashlib.sha1()
    m.update('TCPA')

    seed = os.urandom(20)
    seedstart = 1
    seedend = seedstart + m.digest_size

    output = bytearray(keylen)
    output[0] = 0
    output[seedstart:seedend] = seed

    shastart = 21
    shaend = 21 + m.digest_size
    output[shastart:shaend] = m.digest()

    output[-(len(plaintext)+1)] = 1
    offset = keylen - len(plaintext)
    output[offset:keylen] = plaintext

    dbmask = mgf1(seed, keylen - m.digest_size - 1)
    for i in range(shastart, keylen):
        output[i] ^= dbmask[i - shastart]

    seedmask = mgf1(output[seedend:keylen], m.digest_size)
    for i in range(seedstart, seedend):
        output[i] ^= seedmask[i-1]

    return output

def get_ek(context):
    """Retrieve the raw Endorsement Key from the TPM.

    :param context: The TSS context to use
    :returns: a TspiObject representing the Endorsement Key
    """
    tpm = context.get_tpm_object()
    try:
        return tpm.get_pub_endorsement_key()
    except tspi_exceptions.TSS_E_POLICY_NO_SECRET:
        policy = context.create_policy(TSS_POLICY_USAGE)
        policy.set_secret(TSS_SECRET_MODE_SHA1, well_known_secret)
        policy.assign(tpm)
        return tpm.get_pub_endorsement_key()

def get_ekcert(context):
    """Retrieve the Endoresement Key's certificate from the TPM.

    :param context: The TSS context to use
    :returns: a bytearray containing the x509 certificate
    """
    nvIndex = TSS_NV_DEFINED | TPM_NV_INDEX_EKCert

    nv = context.create_nv(0)
    nv.set_index(nvIndex)

    # Try reading without authentication, and then fall back to using the
    # well known secret
    try:
        blob = nv.read_value(0, 5)
    except tspi_exceptions.TPM_E_AUTH_CONFLICT:
        policy = context.create_policy(TSS_POLICY_USAGE)
        policy.set_secret(TSS_SECRET_MODE_SHA1, well_known_secret)
        policy.assign(nv)
        blob = nv.read_value(0, 5)

    # Verify that the certificate is well formed
    tag = blob[0] << 8 | blob[1]
    if tag != 0x1001:
            print("Invalid tag %x %x\n" % (blob[0], blob[1]))
            return None

    certtype = blob[2]
    if certtype != 0:
            print("Not a full certificate\n")
            return None

    ekbuflen = blob[3] << 8 | blob[4]
    offset = 5

    blob = nv.read_value(offset, 2)
    if len(blob) < 2:
        print("Invalid length")
        return None

    tag = blob[0] << 8 | blob[1]
    if tag == 0x1002:
        offset += 2
        ekbuflen -= 2
    elif blob[0] != 0x30:
        print("Invalid header %x %x" % (blob[0], blob[1]))
        return None

    ekbuf = bytearray()
    ekoffset = 0

    while ekoffset < ekbuflen:
        length = ekbuflen-ekoffset
        if length > 128:
            length = 128
        blob = nv.read_value(offset, length)
        ekbuf += blob
        offset += len(blob)
        ekoffset += len(blob)

    return ekbuf


def create_aik(context):
    """Ask the TPM to create an Authorisation Identity Key

    :param context: The TSS context to use
    :returns: a tuple containing the RSA public key and a TSS key blob
    """

    n = bytearray([0xff] * (2048/8))

    srk = context.load_key_by_uuid(TSS_PS_TYPE_SYSTEM, srk_uuid)

    keypolicy = srk.get_policy_object(TSS_POLICY_USAGE)
    keypolicy.set_secret(TSS_SECRET_MODE_SHA1, well_known_secret)

    tpm = context.get_tpm_object()
    tpmpolicy = context.create_policy(TSS_POLICY_USAGE)
    tpmpolicy.assign(tpm)
    tpmpolicy.set_secret(TSS_SECRET_MODE_SHA1, well_known_secret)

    pcakey = context.create_rsa_key(TSS_KEY_TYPE_LEGACY|TSS_KEY_SIZE_2048)
    pcakey.set_modulus(n)

    aik = context.create_rsa_key(TSS_KEY_TYPE_IDENTITY|TSS_KEY_SIZE_2048)

    data = tpm.collate_identity_request(srk, pcakey, aik)

    pubkey = aik.get_pubkeyblob()
    blob = aik.get_keyblob()

    return (pubkey, blob)


def verify_ek(context, ekcert):
    """Verify that the provided EK certificate is signed by a trusted root

    :param context: The TSS context to use
    :param ekcert: The Endorsement Key certificate
    :returns: True if the certificate can be verified, false otherwise
    """
    ek509 = x509.load_der_x509_certificate(ekcert, default_backend())
    for signer in trusted_certs:
        signcert = x509.load_pem_x509_certificate(trusted_certs[signer],
                                                  default_backend())
        signkey = signcert.public_key()

        # X509 does not support validation/verification in pyca/cryptography
        # open issue: https://github.com/pyca/cryptography/issues/2381

        # Check if the EKCERT was signed by one of the trusted certs
        # if ek509.verify(signkey) == 1:
        #    return True

    for key in trusted_keys:

        e = int(trusted_keys[key]['exponent'], 16)
        n = int(binascii.hexlify(trusted_keys[key]['key'], 16))

        public_num = rsa.RSAPublicNumbers(e, n)
        pubkey = public_num.public_key(default_backend())

        # X509 does not support validation/verification in pyca/cryptography
        # open issue: https://github.com/pyca/cryptography/issues/2381

        # Check if the EKCERT was signed by one of the trusted keys
        # if ek509.verify(pubkey) == 1:
        #    return True

    return False


def generate_challenge(context, ekcert, aikpub, secret, ek=None):
    """ Generate a challenge to verify that the AIK is under the control of
    the TPM we're talking to.

    :param context: The TSS context to use
    :param ekcert: The Endorsement Key certificate
    :param aikpub: The public Attestation Identity Key blob
    :param secret: The secret to challenge the TPM with
    :param ek: TspiKey representing ek. ekcert is ignored if ek is provided.

    :returns: a tuple containing the asymmetric and symmetric components of
    the challenge
    """

    aeskey = bytearray(os.urandom(16))
    iv = bytearray(os.urandom(16))

    if ek is None:
        # Replace rsaesOaep OID with rsaEncryption
        ekcert = ekcert.replace('\x2a\x86\x48\x86\xf7\x0d\x01\x01\x07',
                                '\x2a\x86\x48\x86\xf7\x0d\x01\x01\x01')

        x509_cert = x509.load_der_x509_certificate(ekcert)
        rsakey = x509_cert.public_key()
        assert isinstance(rsakey, rsa.RSAPublicKey)

    else:
        ek_pubkey = ek.public_key()
        e = int('010001', 16)
        n = int(binascii.hexlify(ek_pubkey), 16)
        public_num = rsa.RSAPublicNumbers(e, n)
        rsakey = public_num.public_key(default_backend())

    # TPM_ALG_AES, TPM_ES_SYM_CBC_PKCS5PAD, key length
    asymplain = bytearray([0x00, 0x00, 0x00, 0x06, 0x00, 0xff, 0x00, 0x10])
    asymplain += aeskey

    m = hashlib.sha1()
    m.update(aikpub)
    asymplain += m.digest()

    # Pad with the TCG varient of OAEP
    asymplain = tpm_oaep(asymplain, len(rsakey)/8)

    # Generate the EKpub-encrypted asymmetric buffer containing the aes key
    asymenc = bytearray(
                rsakey.encrypt(
                    asymplain,
                    padding.MGF1(algorithm=hashes.SHA1())
                    )
                )

    # And symmetrically encrypt the secret with AES
    cipher = Cipher(algorithms.AES(aeskey), modes.CBC(iv), default_backend())
    encryptor = cipher.encryptor()
    symenc = encryptor.update(secret) + encryptor.finalize()

    symheader = struct.pack('!llhhllll', len(symenc) + len(iv),
                            TPM_ALG_AES, TPM_ES_SYM_CBC_PKCS5PAD,
                            TPM_SS_NONE, 12, 128, len(iv), 0)
    symenc = symheader + iv + symenc

    return (asymenc, symenc)


def aik_challenge_response(context, aikblob, asymchallenge, symchallenge):
    """Ask the TPM to respond to a challenge

    :param context: The TSS context to use
    :param aikblob: The Attestation Identity Key blob
    :param asymchallenge: The asymmetrically encrypted challenge
    :param symchallenge: The symmertrically encrypted challenge
    :returns: The decrypted challenge
    """

    srk = context.load_key_by_uuid(TSS_PS_TYPE_SYSTEM, srk_uuid)
    srkpolicy = srk.get_policy_object(TSS_POLICY_USAGE)
    srkpolicy.set_secret(TSS_SECRET_MODE_SHA1, well_known_secret)

    tpm = context.get_tpm_object()
    tpmpolicy = context.create_policy(TSS_POLICY_USAGE)
    tpmpolicy.assign(tpm)
    tpmpolicy.set_secret(TSS_SECRET_MODE_SHA1, well_known_secret)

    aik = context.load_key_by_blob(srk, aikblob)

    try:
        return tpm.activate_identity(aik, asymchallenge, symchallenge)
    except tspi_exceptions.TPM_E_DECRYPT_ERROR:
        return None


def quote_verify(data, validation, aik, pcrvalues):
    """Verify that a generated quote came from a trusted TPM and matches the
    previously obtained PCR values

    :param data: The TPM_QUOTE_INFO structure provided by the TPM
    :param validation: The validation information provided by the TPM
    :param aik: The object representing the Attestation Identity Key
    :param pcrvalues: A dictionary containing the PCRs read from the TPM
    :returns: True if the quote can be verified, False otherwise
    """
    select = 0
    maxpcr = 0

    m = hashlib.sha1()
    m.update(data)
    md = m.digest()

    # Verify that the validation blob was generated by a trusted TPM
    aik_pubkey = aik.get_pubkey()

    e = int('010001', 16)
    n = int(binascii.hexlify(aik_pubkey), 16)
    public_num = rsa.RSAPublicNumbers(e, n)
    pubkey = public_num.public_key(default_backend())

    try:
        ret = pubkey.verify(
            str(validation),
            md,
            padding.PSS(mgf=padding.MGF1(hashes.SHA1()),
                        salt_length=padding.PSS.MAX_LENGTH)
            hashes.SHA1()
        )
    except crypto_exceptions.InvalidKey:
        return False

    # And then verify that the validation blob corresponds to the PCR
    # values we have
    values = bytearray()

    for pcr in sorted(pcrvalues):
        values += pcrvalues[pcr]
        select |= (1 << pcr)
        maxpcr = pcr

    if maxpcr < 16:
        header = struct.pack('!H', 2)
        header += struct.pack('@H', select)
        header += struct.pack('!I', len(values))
    else:
        header = struct.pack('!H', 4)
        header += struct.pack('@I', select)
        header += struct.pack('!I', len(values))

    pcr_blob = header + values

    m = hashlib.sha1()
    m.update(pcr_blob)
    pcr_hash = m.digest()

    if pcr_hash == data[8:28]:
        return True
    else:
        return False


def take_ownership(context):
    """Take ownership of a TPM

    :param context: The TSS context to use

    :returns: True on ownership being taken, False if the TPM is already owned
    """

    tpm = context.get_tpm_object()
    tpmpolicy = tpm.get_policy_object(TSS_POLICY_USAGE)
    tpmpolicy.set_secret(TSS_SECRET_MODE_SHA1, well_known_secret)

    srk = context.create_rsa_key(TSS_KEY_TSP_SRK | TSS_KEY_AUTHORIZATION)
    srkpolicy = srk.get_policy_object(TSS_POLICY_USAGE)
    srkpolicy.set_secret(TSS_SECRET_MODE_SHA1, well_known_secret)

    try:
        tpm.take_ownership(srk)
    except tspi_exceptions.TPM_E_DISABLED_CMD:
        return False

    return True
