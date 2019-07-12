# procedures
This file contains a small number of procedures that can be run on an interactive shell of the SVM

# password_change
This procedures changes the password of a local user on the SVM. You will most likely want to change the password of the 'vsadmin' user.
##### Inputs
1. SVM_IP; The IP address of the SVM
2. USER; The user that needs its password changed. Most likely the vsadmin user.
3. OLD_PASS; The old password
4. NEW_PASS; The new password
##### Procedure
1. SSH to the SVM.
<pre>
ssh USER@SVM_IP
Password: OLD_PASS
</pre>
2. Change the password.
<pre>
security login password -username USER
Enter your current password: OLD_PASS
Enter a new password: NEW_PASS
Enter it again: NEW_PASS
</pre>
3. Logout of the SVM.
<pre>
exit
Goodbye
</pre>
###### END

# install_client_certificate
This procedure installs a client certificate in the SVM. The CN of the certificate must match the local user in the SVM that you 
want to enable certificate-based authentication for.
###### Inputs
1. SVM_IP; The IP address of the SVM
2. USER; The local user in the SVM that needs certificate-based authentication
3. PASS; The password for the vsadmin user
4. CERT_PEM; The PEM file for a certificate to be used for authentication
###### Procedure
1. From a Linux machine, check that CN of the certificate contains the name of USER. This example will use 'vsadmin'
<pre>
keytool -printcert -file CERT_PEM | grep Own
Owner: CN=vsadmin, O=NetApp, L=RTP, ST=NC, C=US
</pre>
2. Display the PEM file. The output below is an example.
<pre>
cat CERT_PEM
-----BEGIN CERTIFICATE-----
MIIDaTCCAlGgAwIBAgIJAL8rRcoZCb6eMA0GCSqGSIb3DQEBCwUAMEsxCzAJBgNV
BAYTAlVTMQswCQYDVQQIDAJOQzEMMAoGA1UEBwwDUlRQMQ8wDQYDVQQKDAZOZXRB
cHAxEDAOBgNVBAMMB3ZzYWRtaW4wHhcNMTkwNTI0MDU0NDAxWhcNMjIwNTIzMDU0
NDAxWjBLMQswCQYDVQQGEwJVUzELMAkGA1UECAwCTkMxDDAKBgNVBAcMA1JUUDEP
MA0GA1UECgwGTmV0QXBwMRAwDgYDVQQDDAd2c2FkbWluMIIBIjANBgkqhkiG9w0B
AQEFAAOCAQ8AMIIBCgKCAQEAqQ+agb7QY3WshRU54P4QKAOlZsCMkewwqeZRMZ8F
3ud3hz8mp/N7ISm8rOhUIywlE66oxiO36or8RvgbN6L7NqTEAq4pmQjvH5KYzXdY
VQVNbzSXL2CpjuqGcZ6hZvLXroZ3N4OA94RZh16RVvzErwpihXiAeKmwqhQy9GNJ
RKmdtMOvb8p0lkWhNYnEDwIIutvbUgeJhkL4D3+UX+aBh9DDsx3+KnTvOM4f8/Cp
YxCP8NljieuutjP8rie2qtNlUAljx8TnqmhObxmwiNnbkZ6h/gQCrDplL8qcQpnq
NOD0uerTSVnecZqae+ffQuWzpyW+4M3QZQBBY2RAkVWAYwIDAQABo1AwTjAdBgNV
HQ4EFgQUe6R4LFSDa7JIB7wYbVn6dRjhtuAwHwYDVR0jBBgwFoAUe6R4LFSDa7JI
B7wYbVn6dRjhtuAwDAYDVR0TBAUwAwEB/zANBgkqhkiG9w0BAQsFAAOCAQEAH68p
NZZl97rScLRF8taz1m0WzS8djTEv4gvXCjepRUGkWQj/dCbruC5ZFn6XwIDjf+s8
j3s53abPcp/tkT9DDoV9+9Frk1RoJW3M24fKFetvpnYXgAL6GiSguqzZb73PG87p
m7ybURz3ZXUDlKDyWaws8SA7/ZmyU0nn78sVAEaH8CL5iIWu08e3InOrrRdi4buR
nNSEhxEicNRVRpCyqn/welbx68bosGlcmWw9mLKRFW12kl6ZMUs3m7eljsAprItT
i1/1lidIqPZFIn+uKeHkMuh7w+RyhTxOTjwqDQKWn7z7EBx7HR4DOkgZlnpUkmkB
oVXFXKONCGg3pGZ3Vw==
-----END CERTIFICATE-----
</pre>
3. SSH to the SVM.
<pre>
ssh vsadmin@SVM_IP
Password: PASS
</pre>
4. Install the certificate. Paste the output of the CERT_PEM file from step two and then press enter. 
<pre>
security certificate install -type client-ca
Please enter Certificate: Press <Enter> when done
-----BEGIN CERTIFICATE-----
MIIDaTCCAlGgAwIBAgIJAL8rRcoZCb6eMA0GCSqGSIb3DQEBCwUAMEsxCzAJBgNV
BAYTAlVTMQswCQYDVQQIDAJOQzEMMAoGA1UEBwwDUlRQMQ8wDQYDVQQKDAZOZXRB
cHAxEDAOBgNVBAMMB3ZzYWRtaW4wHhcNMTkwNTI0MDU0NDAxWhcNMjIwNTIzMDU0
NDAxWjBLMQswCQYDVQQGEwJVUzELMAkGA1UECAwCTkMxDDAKBgNVBAcMA1JUUDEP
MA0GA1UECgwGTmV0QXBwMRAwDgYDVQQDDAd2c2FkbWluMIIBIjANBgkqhkiG9w0B
AQEFAAOCAQ8AMIIBCgKCAQEAqQ+agb7QY3WshRU54P4QKAOlZsCMkewwqeZRMZ8F
3ud3hz8mp/N7ISm8rOhUIywlE66oxiO36or8RvgbN6L7NqTEAq4pmQjvH5KYzXdY
VQVNbzSXL2CpjuqGcZ6hZvLXroZ3N4OA94RZh16RVvzErwpihXiAeKmwqhQy9GNJ
RKmdtMOvb8p0lkWhNYnEDwIIutvbUgeJhkL4D3+UX+aBh9DDsx3+KnTvOM4f8/Cp
YxCP8NljieuutjP8rie2qtNlUAljx8TnqmhObxmwiNnbkZ6h/gQCrDplL8qcQpnq
NOD0uerTSVnecZqae+ffQuWzpyW+4M3QZQBBY2RAkVWAYwIDAQABo1AwTjAdBgNV
HQ4EFgQUe6R4LFSDa7JIB7wYbVn6dRjhtuAwHwYDVR0jBBgwFoAUe6R4LFSDa7JI
B7wYbVn6dRjhtuAwDAYDVR0TBAUwAwEB/zANBgkqhkiG9w0BAQsFAAOCAQEAH68p
NZZl97rScLRF8taz1m0WzS8djTEv4gvXCjepRUGkWQj/dCbruC5ZFn6XwIDjf+s8
j3s53abPcp/tkT9DDoV9+9Frk1RoJW3M24fKFetvpnYXgAL6GiSguqzZb73PG87p
m7ybURz3ZXUDlKDyWaws8SA7/ZmyU0nn78sVAEaH8CL5iIWu08e3InOrrRdi4buR
nNSEhxEicNRVRpCyqn/welbx68bosGlcmWw9mLKRFW12kl6ZMUs3m7eljsAprItT
i1/1lidIqPZFIn+uKeHkMuh7w+RyhTxOTjwqDQKWn7z7EBx7HR4DOkgZlnpUkmkB
oVXFXKONCGg3pGZ3Vw==
-----END CERTIFICATE-----
You should keep a copy of the CA-signed digital certificate for future reference.
The installed certificate's CA and serial number for reference:
CA: vsadmin
Serial: BF2B45CA1909BE9E
The certificate's generated name for reference: vsadmin
</pre>
5. Ensure that SSL is enabled to use client certificates for authentication.
<pre>
security ssl modify -client-enabled true
</pre>
6. Logout of the SVM.
<pre>
exit
Goodbye
</pre>
###### END
