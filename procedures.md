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
