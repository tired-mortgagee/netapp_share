NaElement.py                                                                                        0000644 0000000 0000000 00000027477 13452554241 012024  0                                                                                                    ustar   root                            root                                                                                                                                                                                                                   #============================================================#
#                                                            #
# $ID$                                                       #
#                                                            #
# NaElement.py                                               #
#                                                            #
# Operations on ONTAPI and DataFabric Manager elements       #
#                                                            #
# Copyright (c) 2011 NetApp, Inc. All rights reserved.       #
# Specifications subject to change without notice.           #
#                                                            #
#============================================================#

__version__ = 1.0


import re
import sys

class NaElement :
    """Class encapsulating Netapp XML request elements.

    An NaElement encapsulates one level of an XML element.
    Elements can be arbitrarily nested.  They have names,
    corresponding to XML tags, attributes (only used for
    results), values (always strings) and possibly children,
    corresponding to nested tagged items.  See NaServer for
    instructions on using NaElements to invoke ONTAPI API calls.

    The following routines are available for constructing and
    accessing the contents of NaElements.
    """ 


    #Global Variables
    DEFAULT_KEY = "#u82fyi8S5\017pPemw"
    MAX_CHUNK_SIZE = 256


    def __init__(self, name, value=None):
        """Construct a new NaElement.  The 'value' parameter is
        optional for top level elements.
        """ 

        self.element = {'name':name,'content':"",'children':[],'attrkeys':[],'attrvals':[]}
        if (value != None) :
            self.element['content'] = value


    def results_status(self) :
        """Indicates success or failure of API call.
        Returns either 'passed' or 'failed'.
        """ 
        r = self.attr_get("status")

        if(r == "passed"):
            return "passed"

        else :
            return "failed"


    def results_reason(self):
        """Human-readable string describing a failure.
        Only present if results_status does not return 'passed'.
        """ 

        r = self.attr_get("status")
        if(r == "passed"):
            return None

        r = self.attr_get("reason")
        if not r:
            return "No reason given"

        return str(r)


    def results_errno(self):
        """Returns an error number, 0 on success.
        """ 

        r = self.attr_get("status")

        if (r == "passed"):
            return 0

        r = self.attr_get("errno")

        if not r:
            r = -1

        return r


    def child_get(self, name):
        """Get a named child of an element, which is also an
        element.  Elements can be nested arbitrarily, so
        the element you get with this could also have other
        children.  The return is either an NaElement named
        'name', or None if none is found.
        """ 

        arr = self.element['children']

        for i in arr :

            if(name == i.element['name']):
                return i

        return None


    def set_content(self, content):
        """Set the element's value to 'content'.  This is
        not needed in normal development.
        """ 

        self.element['content'] = content


    def add_content(self, content):
        """Add the element's value to 'content'.  This is
        not needed in normal development.
        """ 

        self.element['content'] = self.element['content']+content
        return



    def has_children(self):
        """Returns 1 if the element has any children, 0 otherwise
        """ 

        arr = self.element['children']

        if(len(arr)>0):
            return 1

        else :
            return 0



    def child_add(self, child):
        """Add the element 'child' to the children list of
        the current object, which is also an element.
        """ 

        arr = self.element['children']
        arr.append(child)
        self.element['children'] = arr



    def child_add_string(self, name, value):
        """Construct an element with name 'name' and contents
        'value', and add it to the current object, which
        is also an element.
        """ 

        elt = NaElement(name,value)
        self.child_add(elt)



    def child_get_string(self, name):
        """Gets the child named 'name' from the current object
        and returns its value.  If no child named 'name' is
        found, returns None.
        """ 

        elts = self.element['children']

        for elt in elts:
            if (name == elt.element['name']):
                return elt.element['content']

        return None



    def child_get_int(self, child):
        """Gets the child named 'name' from the current object
        and returns its value as an integer.  If no child
        named 'name' is found, returns None.
        """ 

        temp =  self.child_get_string(child)
        return int(temp)



    def children_get(self):
        """Returns the list of children as an array.
        """ 

        elts = self.element['children']
        return elts



    def sprintf(self, indent=""):
        """Sprintf pretty-prints the element and its children,
        recursively, in XML-ish format.  This is of use
        mainly in exploratory and utility programs.  Use
        child_get_string() to dig values out of a top-level
        element's children.

        Parameter 'indent' is optional.
        """ 

        name = self.element['name']
        s = indent+"<"+name
        keys = self.element['attrkeys']
        vals = self.element['attrvals']
        j = 0

        for i in keys:
            s = s+" "+str(i)+"=\""+str(vals[j])+"\""
            j = j+1

        s = s+">"
        children = self.element['children']

        if(len(children) > 0):
            s = s+"\n"

        for i in children:
            c = i

            if (not re.search('NaElement.NaElement', str(c.__class__), re.I)):
                sys.exit("Unexpected reference found, expected NaElement.NaElement not "+ str(c.__class__)+"\n")

            s = s+c.sprintf(indent + "\t")

        self.element['content'] = NaElement.escapeHTML(self.element['content'])
        s = s + str(self.element['content'])

        if(len(children) > 0):
            s = s+indent

        s = s+"</"+name+">\n"
        return s



    def child_add_string_encrypted(self, name, value, key=None):
        """Same as child_add_string, but encrypts 'value'
        with 'key' before adding the element to the current
        object.  This is only used at present for certain
        key exchange operations.  Both client and server
        must know the value of 'key' and agree to use this
        routine and its companion, child_get_string_encrypted().
        The default key will be used if the given key is None.
        """ 

        if(not name or not value):
            sys.exit("Invalid input specified for name or value")

        if (key == None):
            key = self.DEFAULT_KEY

        if (len(key) != 16):
            sys.exit("Invalid key, key length sholud be 16")

        #encryption of key and others
        encrypted_value = self.RC4(key,value)
        self.child_add_string(name,unpack('H*',encrypted_value))



    def child_get_string_encrypted(self, name, key=None):
        """Get the value of child named 'name', and decrypt
        it with 'key' before returning it.
        The default key will be used if the given key is None.
        """ 

        if (key == None):
            key = self.DEFAULT_KEY

        if (len(key) != 16):
             sys.exit("Invalid key, key length sholud be 16")

        value = self.child_get_string(name)
        plaintext = self.RC4(key,pack('H*',value))
        return plaintext



    def toEncodedString(self):
        """Encodes string embedded with special chars like &,<,>.
        This is mainly useful when passing string values embedded
        with special chars like &,<,> to API.

        Example :
        server.invoke("qtree-create","qtree","abc<qt0","volume","vol0")
        """ 
        n = self.element['name']
        s = "<"+n
        keys = self.element['attrkeys']
        vals = self.element['attrvals']
        j = 0

        for i in keys :
            s = s+" "+str(i)+"=\""+str(vals[j])+"\""
            j = j+1

        s = s+">"
        children = self.element['children']

        for i in children :
            c = i
                      
            if (not re.search("NaElement.NaElement",str(c.__class__),re.I)):
                sys.exit("Unexpected reference found, expected NaElement.NaElement not "+ str(c.__class__)+"\n")

            s = s+c.toEncodedString()

        cont = str(self.element['content'])
        cont = NaElement.escapeHTML(cont)
        s = s+cont
        s = s+"</"+n+">"
        return s



#------------------------------------------------------------#
#
# routines beyond this point are "private"
#
#------------------------------------------------------------#

    @staticmethod 
    
    def escapeHTML(cont):
        """ This is a private function, not to be called externally.
        This method converts reserved HTML characters to corresponding entity names.
        """

        cont = re.sub(r'&','&amp;',cont,count=0)
        cont = re.sub(r'<','&lt;',cont,count=0)
        cont = re.sub(r'>','&gt;',cont,count=0)
        cont = re.sub(r"'",'&apos;',cont,count=0)
        cont = re.sub(r'"','&quot;',cont,count=0)

        """ The existence of '&' (ampersand) sign in entity names implies that multiple calls
	to this function will result in non-idempotent encoding. So, to handle such situation
	or when the input itself contains entity names, we reconvert such recurrences to
	appropriate characters.
        """
        cont = re.sub(r'&amp;amp;','&amp;',cont,count=0)
        cont = re.sub(r'&amp;lt;','&lt;',cont,count=0)
        cont = re.sub(r'&amp;gt;','&gt;',cont,count=0)
        cont = re.sub(r'&amp;apos;','&apos;',cont,count=0)
        cont = re.sub(r'&amp;quot;','&quot;',cont,count=0)
        return cont

    def RC4(self, key, value):
        """This is a private function, not to be called from outside NaElement.
        """ 

        box = self.prepare_key(key)
        x,y = 0,0
        plaintext = value
        num = len(plaintext)/self.MAX_CHUNK_SIZE

        integer = int(num)

        if(integer == num):
            num_pieces = integer

        else :
            num_pieces = integer+1

        for piece in range(0,num_pieces-1):
            plaintext = unpack("C*",plaintext[piece * self.MAX_CHUNK_SIZE:(piece*self.MAX_CHUNK_SIZE)+self.MAX_CHUNK_SIZE])

            for i in plaintext:

                if ((x+1) > 255 ):
                    x = 0

                y = y+box[x]

                if(y > 255):
                    y = -256

                box[x],box[y] = box[y],box[x]
                plain_text.append(chr(ord(char) ^ box[(box[x] + box[y]) % 256]))

        return plain_text



    def prepare_key(self, key):
        """This is a private function, not to be called from outside NaElement.
        """ 

        k = unpack('C*',key)
        box = range(255)
        y = 0

        for x in range(255):
            y = (k[x % k]+ box[x] + y) % 256
            box[x],box[y] = box[y],box[x]

        return box



    def attr_set(self, key, value):
        """This is a private function, not to be called from outside NaElement.
        """ 

        arr = self.element['attrkeys']
        arr.append(key)
        self.element['attrkeys'] = arr
        arr = self.element['attrvals']
        arr.append(value)
        self.element['attrvals'] = arr



    def attr_get(self, key):
        """This is a private function, not to be called from outside NaElement.
        """ 

        keys = self.element['attrkeys']
        vals = self.element['attrvals']
        j = 0

        for i in keys:
            if(i == key):
                return vals[j]

            j = j+1

        return None
                                                                                                                                                                                                 NaElement.pyc                                                                                       0000644 0000000 0000000 00000026775 13452554441 012171  0                                                                                                    ustar   root                            root                                                                                                                                                                                                                   �
�ت\c           @   s5   d  Z  d d l Z d d l Z d d d �  �  YZ d S(   g      �?i����Nt	   NaElementc           B   s�   e  Z d  Z d Z d Z d d � Z d �  Z d �  Z d �  Z	 d �  Z
 d �  Z d	 �  Z d
 �  Z d �  Z d �  Z d �  Z d �  Z d �  Z d d � Z d d � Z d d � Z d �  Z e d �  � Z d �  Z d �  Z d �  Z d �  Z RS(   s  Class encapsulating Netapp XML request elements.

    An NaElement encapsulates one level of an XML element.
    Elements can be arbitrarily nested.  They have names,
    corresponding to XML tags, attributes (only used for
    results), values (always strings) and possibly children,
    corresponding to nested tagged items.  See NaServer for
    instructions on using NaElements to invoke ONTAPI API calls.

    The following routines are available for constructing and
    accessing the contents of NaElements.
    s   #u82fyi8S5pPemwi   c         C   sL   i | d 6d d 6g  d 6g  d 6g  d 6|  _  | d k rH | |  j  d <n  d S(   sf   Construct a new NaElement.  The 'value' parameter is
        optional for top level elements.
        t   namet    t   contentt   childrent   attrkeyst   attrvalsN(   t   elementt   None(   t   selfR   t   value(    (    s   /root/src/manila/NaElement.pyt   __init__(   s    ,c         C   s'   |  j  d � } | d k r d Sd Sd S(   s_   Indicates success or failure of API call.
        Returns either 'passed' or 'failed'.
        t   statust   passedt   failedN(   t   attr_get(   R	   t   r(    (    s   /root/src/manila/NaElement.pyt   results_status2   s    c         C   sB   |  j  d � } | d k r d S|  j  d � } | s8 d St | � S(   su   Human-readable string describing a failure.
        Only present if results_status does not return 'passed'.
        R   R   t   reasons   No reason givenN(   R   R   t   str(   R	   R   (    (    s   /root/src/manila/NaElement.pyt   results_reason?   s    c         C   sA   |  j  d � } | d k r d S|  j  d � } | s= d } n  | S(   s/   Returns an error number, 0 on success.
        R   R   i    t   errnoi����(   R   (   R	   R   (    (    s   /root/src/manila/NaElement.pyt   results_errnoO   s    	c         C   s9   |  j  d } x% | D] } | | j  d k r | Sq Wd S(   s  Get a named child of an element, which is also an
        element.  Elements can be nested arbitrarily, so
        the element you get with this could also have other
        children.  The return is either an NaElement named
        'name', or None if none is found.
        R   R   N(   R   R   (   R	   R   t   arrt   i(    (    s   /root/src/manila/NaElement.pyt	   child_get`   s
    c         C   s   | |  j  d <d S(   sa   Set the element's value to 'content'.  This is
        not needed in normal development.
        R   N(   R   (   R	   R   (    (    s   /root/src/manila/NaElement.pyt   set_contentr   s    c         C   s   |  j  d | |  j  d <d S(   sa   Add the element's value to 'content'.  This is
        not needed in normal development.
        R   N(   R   (   R	   R   (    (    s   /root/src/manila/NaElement.pyt   add_contentz   s    c         C   s+   |  j  d } t | � d k r# d Sd Sd S(   s?   Returns 1 if the element has any children, 0 otherwise
        R   i    i   N(   R   t   len(   R	   R   (    (    s   /root/src/manila/NaElement.pyt   has_children�   s    c         C   s+   |  j  d } | j | � | |  j  d <d S(   sn   Add the element 'child' to the children list of
        the current object, which is also an element.
        R   N(   R   t   append(   R	   t   childR   (    (    s   /root/src/manila/NaElement.pyt	   child_add�   s    c         C   s    t  | | � } |  j | � d S(   s�   Construct an element with name 'name' and contents
        'value', and add it to the current object, which
        is also an element.
        N(   R    R    (   R	   R   R
   t   elt(    (    s   /root/src/manila/NaElement.pyt   child_add_string�   s    c         C   s@   |  j  d } x, | D]$ } | | j  d k r | j  d Sq Wd S(   s�   Gets the child named 'name' from the current object
        and returns its value.  If no child named 'name' is
        found, returns None.
        R   R   R   N(   R   R   (   R	   R   t   eltsR!   (    (    s   /root/src/manila/NaElement.pyt   child_get_string�   s
    c         C   s   |  j  | � } t | � S(   s�   Gets the child named 'name' from the current object
        and returns its value as an integer.  If no child
        named 'name' is found, returns None.
        (   R$   t   int(   R	   R   t   temp(    (    s   /root/src/manila/NaElement.pyt   child_get_int�   s    c         C   s   |  j  d } | S(   s2   Returns the list of children as an array.
        R   (   R   (   R	   R#   (    (    s   /root/src/manila/NaElement.pyt   children_get�   s    R   c   
      C   s�  |  j  d } | d | } |  j  d } |  j  d } d } xB | D]: } | d t | � d t | | � d } | d	 } qB W| d
 } |  j  d } t | � d k r� | d } n  xm | D]e } | }	 t j d t |	 j � t j � st j d t |	 j � d � n  | |	 j	 | d � } q� Wt
 j |  j  d � |  j  d <| t |  j  d � } t | � d k ry| | } n  | d | d } | S(   s.  Sprintf pretty-prints the element and its children,
        recursively, in XML-ish format.  This is of use
        mainly in exploratory and utility programs.  Use
        child_get_string() to dig values out of a top-level
        element's children.

        Parameter 'indent' is optional.
        R   t   <R   R   i    t    s   ="s   "i   t   >R   s   
s   NaElement.NaElements=   Unexpected reference found, expected NaElement.NaElement not s   	R   s   </s   >
(   R   R   R   t   ret   searcht	   __class__t   It   syst   exitt   sprintfR    t
   escapeHTML(
   R	   t   indentR   t   st   keyst   valst   jR   R   t   c(    (    s   /root/src/manila/NaElement.pyR2   �   s.    
*
!!c         C   s�   | s | r t  j d � n  | d k r6 |  j } n  t | � d k rX t  j d � n  |  j | | � } |  j | t d | � � d S(   s�  Same as child_add_string, but encrypts 'value'
        with 'key' before adding the element to the current
        object.  This is only used at present for certain
        key exchange operations.  Both client and server
        must know the value of 'key' and agree to use this
        routine and its companion, child_get_string_encrypted().
        The default key will be used if the given key is None.
        s)   Invalid input specified for name or valuei   s$   Invalid key, key length sholud be 16s   H*N(   R0   R1   R   t   DEFAULT_KEYR   t   RC4R"   t   unpack(   R	   R   R
   t   keyt   encrypted_value(    (    s   /root/src/manila/NaElement.pyt   child_add_string_encrypted�   s    
c         C   sh   | d k r |  j } n  t | � d k r: t j d � n  |  j | � } |  j | t d | � � } | S(   s�   Get the value of child named 'name', and decrypt
        it with 'key' before returning it.
        The default key will be used if the given key is None.
        i   s$   Invalid key, key length sholud be 16s   H*N(   R   R:   R   R0   R1   R$   R;   t   pack(   R	   R   R=   R
   t	   plaintext(    (    s   /root/src/manila/NaElement.pyt   child_get_string_encrypted  s    c   
      C   s>  |  j  d } d | } |  j  d } |  j  d } d } xB | D]: } | d t | � d t | | � d } | d	 } q> W| d
 } |  j  d } xf | D]^ } | } t j d t | j � t j � s� t j d t | j � d � n  | | j �  } q� Wt |  j  d � }	 t	 j
 |	 � }	 | |	 } | d | d
 } | S(   s
  Encodes string embedded with special chars like &,<,>.
        This is mainly useful when passing string values embedded
        with special chars like &,<,> to API.

        Example :
        server.invoke("qtree-create","qtree","abc<qt0","volume","vol0")
        R   R)   R   R   i    R*   s   ="s   "i   R+   R   s   NaElement.NaElements=   Unexpected reference found, expected NaElement.NaElement not s   
R   s   </(   R   R   R,   R-   R.   R/   R0   R1   t   toEncodedStringR    R3   (
   R	   t   nR5   R6   R7   R8   R   R   R9   t   cont(    (    s   /root/src/manila/NaElement.pyRC   $  s(    
*
!!
c         C   s  t  j d d |  d d �}  t  j d d |  d d �}  t  j d d |  d d �}  t  j d	 d
 |  d d �}  t  j d d |  d d �}  t  j d d |  d d �}  t  j d d |  d d �}  t  j d d |  d d �}  t  j d d
 |  d d �}  t  j d d |  d d �}  |  S(   s�    This is a private function, not to be called externally.
        This method converts reserved HTML characters to corresponding entity names.
        t   &s   &amp;t   counti    R)   s   &lt;R+   s   &gt;t   's   &apos;t   "s   &quot;s	   &amp;amp;s   &amp;lt;s   &amp;gt;s
   &amp;apos;s
   &amp;quot;(   R,   t   sub(   RE   (    (    s   /root/src/manila/NaElement.pyR3   O  s    c      	   C   sG  |  j  | � } d \ } } | } t | � |  j } t | � } | | k rU | }	 n
 | d }	 x� t d |	 d � D]� }
 t d | |
 |  j |
 |  j |  j !� } x� | D]� } | d d k r� d } n  | | | } | d k r� d } n  | | | | | | <| | <t j t t	 t
 � | | | | | d A� � q� Wqs Wt S(   sM   This is a private function, not to be called from outside NaElement.
        i    i   s   C*i�   i ���i   (   i    i    (   t   prepare_keyR   t   MAX_CHUNK_SIZER%   t   rangeR<   t
   plain_textR   t   chrt   ordt   char(   R	   R=   R
   t   boxt   xt   yRA   t   numt   integert
   num_piecest   pieceR   (    (    s   /root/src/manila/NaElement.pyR;   h  s&    	
+		9c         C   sw   t  d | � } t d � } d } xO t d � D]A } | | | | | | d } | | | | | | <| | <q. W| S(   sM   This is a private function, not to be called from outside NaElement.
        s   C*i�   i    i   (   R<   RM   (   R	   R=   t   kRR   RT   RS   (    (    s   /root/src/manila/NaElement.pyRK   �  s    !c         C   sR   |  j  d } | j | � | |  j  d <|  j  d } | j | � | |  j  d <d S(   sM   This is a private function, not to be called from outside NaElement.
        R   R   N(   R   R   (   R	   R=   R
   R   (    (    s   /root/src/manila/NaElement.pyt   attr_set�  s    c         C   sS   |  j  d } |  j  d } d } x, | D]$ } | | k rA | | S| d } q' Wd S(   sM   This is a private function, not to be called from outside NaElement.
        R   R   i    i   N(   R   R   (   R	   R=   R6   R7   R8   R   (    (    s   /root/src/manila/NaElement.pyR   �  s    N(   t   __name__t
   __module__t   __doc__R:   RL   R   R   R   R   R   R   R   R   R   R    R"   R$   R'   R(   R2   R?   RB   RC   t   staticmethodR3   R;   RK   RZ   R   (    (    (    s   /root/src/manila/NaElement.pyR       s2   
						
							-	+	%		(    (   t   __version__R,   R0   R    (    (    (    s   /root/src/manila/NaElement.pyt   <module>   s      NaErrno.py                                                                                          0000644 0000000 0000000 00000106370 13452554242 011507  0                                                                                                    ustar   root                            root                                                                                                                                                                                                                   #
# Copyright (c) 2011 NetApp, Inc.
# All rights reserved.
#
# Generated: Thu Aug 25 17:10:41 2011
#

EONTAPI_EPERM = 1
EONTAPI_ENOENT = 2
EONTAPI_ESRCH = 3
EONTAPI_EINTR = 4
EONTAPI_EIO = 5
EONTAPI_ENXIO = 6
EONTAPI_E2BIG = 7
EONTAPI_ENOEXEC = 8
EONTAPI_EBADF = 9
EONTAPI_ECHILD = 10
EONTAPI_EDEADLK = 11
EONTAPI_ENOMEM = 12
EONTAPI_EACCES = 13
EONTAPI_EFAULT = 14
EONTAPI_ENOTBLK = 15
EONTAPI_EBUSY = 16
EONTAPI_EEXIST = 17
EONTAPI_EXDEV = 18
EONTAPI_ENODEV = 19
EONTAPI_ENOTDIR = 20
EONTAPI_EISDIR = 21
EONTAPI_EINVAL = 22
EONTAPI_ENFILE = 23
EONTAPI_EMFILE = 24
EONTAPI_ENOTTY = 25
EONTAPI_ETXTBSY = 26
EONTAPI_EFBIG = 27
EONTAPI_ENOSPC = 28
EONTAPI_ESPIPE = 29
EONTAPI_EROFS = 30
EONTAPI_EMLINK = 31
EONTAPI_EPIPE = 32
EONTAPI_EDOM = 33
EONTAPI_ERANGE = 34
EONTAPI_EAGAIN = 35
EONTAPI_EINPROGESS = 36
EONTAPI_EALREADY = 37
EONTAPI_ENOTSOCK = 38
EONTAPI_EDESTADDRREQ = 39
EONTAPI_EMSGSIZE = 40
EONTAPI_EPROTOTYPE = 41
EONTAPI_ENOPROTOOPT = 42
EONTAPI_EPROTONOSUPPORT = 43
EONTAPI_ESOCKTNOSUPPORT = 44
EONTAPI_EOPNOTSUPP = 45
EONTAPI_EPFNOSUPPORT = 46
EONTAPI_EAFNOSUPPORT = 47
EONTAPI_EADDRINUSE = 48
EONTAPI_EADDRNOTAVAIL = 49
EONTAPI_ENETDOWN = 50
EONTAPI_ENETUNREACH = 51
EONTAPI_ENETRESET = 52
EONTAPI_ECONNABORTED = 53
EONTAPI_ECONNRESET = 54
EONTAPI_ENOBUFS = 55
EONTAPI_EISCONN = 56
EONTAPI_ENOTCONN = 57
EONTAPI_ESHUTDOWN = 58
EONTAPI_ETOOMANYREFS = 59
EONTAPI_ETIMEDOUT = 60
EONTAPI_ECONNREFUSED = 61
EONTAPI_ELOOP = 62
EONTAPI_ENAMETOOLONG = 63
EONTAPI_EHOSTDOWN = 64
EONTAPI_EHOSTUNREACH = 65
EONTAPI_ENOTEMPTY = 66
EONTAPI_EPROCLIM = 67
EONTAPI_EUSERS = 68
EONTAPI_EDQUOT = 69
EONTAPI_ESTALE = 70
EONTAPI_EREMOTE = 71
EONTAPI_EBADRPC = 72
EONTAPI_ERPCMSGDENIED = 73
EONTAPI_EPROGUNAVAIL = 74
EONTAPI_EPROGMISMATCH = 75
EONTAPI_EPROCUNAVAIL = 76
EONTAPI_ENOLCK = 77
EONTAPI_ENOSYS = 78
EONTAPI_EFTYPE = 79
EONTAPI_EMTUTOOBIG = 80
EONTAPI_EOFFLINE = 81
EONTAPI_EBADSTREAM = 82
EONTAPI_EBADSTREAMDIR = 83
EONTAPI_ELOADCOMPLETE = 84
EONTAPI_EMOUNTING = 85
EONTAPI_EWFLUSH = 99
EONTAPI_EBADPATH = 100
EONTAPI_EBADCHAR = 101
EONTAPI_ESHARECONFLICT = 102
EONTAPI_ELOCKCONFLICT = 103
EONTAPI_ENOTCOVERED = 104
EONTAPI_EBADXINODE = 105
EONTAPI_ENOTXINODE = 106
EONTAPI_EBADOWNER = 107
EONTAPI_ERMTWRITELEN = 108
EONTAPI_EBADRMT = 109
EONTAPI_EKNOWNBADRMT = 110
EONTAPI_ERMTEOF = 111
EONTAPI_EDELPENDING = 112
EONTAPI_ETRUNCATED = 113
EONTAPI_EREJECTED = 114
EONTAPI_EREADONLY = 115
EONTAPI_EPARTNERREJECT = 116
EONTAPI_ETOOCOMPLEX = 117
EONTAPI_EREGX = 118
EONTAPI_EREGXBADVALUE = 119
EONTAPI_EPERSISTENCE = 120
EONTAPI_ESTHREAD = 121
EONTAPI_EDISABLED = 122
EONTAPI_ENOTVSCANNED = 123
EONTAPI_EFABRIC = 124
EONTAPI_ESYSTEMERR = 125
EONTAPI_EGSSAPI = 126
EONTAPI_ERPCGSSSEQNUM = 127
EONTAPI_EPROXYME = 128
EONTAPI_ERSRVCONFLICT = 129
EONTAPI_ERSRVNSUPPORTED = 130
EONTAPI_ENOQTREE = 131
EONTAPI_ENOTLOCKED = 132
EONTAPI_ELOCKCANCELLED = 133
EONTAPI_ENOSPCSNAP = 134
EONTAPI_ENOMORESNAPS = 135
EONTAPI_ERECURSE = 136
EONTAPI_ERECLAIM = 137
EONTAPI_EZEROLENREC = 138
EONTAPI_ENOTFSCREENED = 139
EONTAPI_EISVDISK = 140
EONTAPI_EWAFLMSGABORTED = 141
EONTAPI_EMSGNULLIFY = 142
EONTAPI_ECOMPRESSCHECK = 143
EONTAPI_EVOLSMALL = 144
EONTAPI_EVOLBIG = 145
EONTAPI_EVOLPAIRED = 146
EONTAPI_EVOLNOTFLEX = 147
EONTAPI_EVOLSTALE = 148
EONTAPI_ENOREG = 149
EONTAPI_ENOREGKEY = 150
EONTAPI_ECANNOTDELETE = 151
EONTAPI_EWORMNOCLOCK = 152
EONTAPI_EWORMVOLWORM = 153
EONTAPI_EWORMVOLSLC = 154
EONTAPI_EWORMVOLNOTWORM = 155
EONTAPI_EWORMSNAPLOCKED = 156
EONTAPI_EWORMSNAPRENAME = 157
EONTAPI_EWORMPERIOD = 158
EONTAPI_ENOSPCAGGR = 159
EONTAPI_EVOLOPNOTSUPP = 160
ESWAPFILENOSPACE = 161
EONTAPI_EADMINOPQUIESCED = 198
EONTAPI_EWRONGSTRIPE = 288
EDATAUNRECOVERABLE = 302
ECLONEINPROGRESS = 307
EFILEIO = 1000
EIPV6 = 1001
EMODE = 1002
ENOPARTNERIFC = 1004
EHOST_BADCONFIGURE = 1005
EHOST_TRYAGAIN = 1006
EHOST_MISC = 1007
ECHECKRESULTS = 1008
ELOOPBACK = 1009
ENETMASKINVALID = 1018
EIOCTLERROR = 1019
EBROADCASTINVALID = 1020
EVDISK_ERROR_NOT_IMPLEMENTED = 9000
EVDISK_ERROR_NOT_QTREE_ROOT = 9001
EVDISK_ERROR_NOT_VDISK_TYPE = 9002
EVDISK_ERROR_NO_SUCH_INITGROUP = 9003
EVDISK_ERROR_INITGROUP_EXISTS = 9004
EVDISK_ERROR_NOT_VALID_FC_WWN = 9005
EVDISK_ERROR_NOT_VALID_ISCSI_NAME = 9006
EVDISK_ERROR_NODE_NOT_IN_INITGROUP = 9007
EVDISK_ERROR_INITGROUP_HAS_NODE = 9008
EVDISK_ERROR_LUN_MAPPING_CONFLICT = 9009
EVDISK_ERROR_INITGROUP_WRONG_TYPE = 9010
EVDISK_ERROR_NO_SUCH_ATTRIBUTE = 9011
EVDISK_ERROR_VDISK_EXISTS = 9012
EVDISK_ERROR_VDISK_EXPORTED = 9013
EVDISK_ERROR_VDISK_NOT_ENABLED = 9014
EVDISK_ERROR_VDISK_NOT_DISABLED = 9015
EVDISK_ERROR_NO_SUCH_LUNMAP = 9016
EVDISK_ERROR_NO_SUCH_VDISK = 9017
EVDISK_ERROR_NOT_IN_SAME_QTREE = 9018
EVDISK_ERROR_SOURCE_IS_VDISK = 9019
EVDISK_ERROR_NO_SUCH_DIRECTORY = 9020
EVDISK_ERROR_INVALID_SNAPSHOT_PATH = 9021
EVDISK_ERROR_NOT_IN_SAME_VOLUME = 9022
EVDISK_ERROR_INITGROUP_HAS_VDISK = 9023
EVDISK_ERROR_INITGROUP_HAS_LUN = 9024
EVDISK_ERROR_INITGROUP_MISSING_ARGS = 9025
EVDISK_ERROR_INITGROUP_INVALID_ATTR_TYPE = 9026
EVDISK_ERROR_INITGROUP_INVALID_ATTR_VALUE = 9027
EVDISK_ERROR_NO_EXPORTED_VDISK_SHARE_WRITE = 9028
EVDISK_ERROR_INITGROUP_MAPS_EXIST = 9029
EVDISK_ERROR_VOLUME_NOT_SPACE_RESERVED = 9030
EVDISK_ERROR_SNAPSHOT_FILE_NOT_VDISK = 9031
EVDISK_ERROR_NITGROUP_INVALID_ATTR_VALUE_OS_TYPE = 9032
EVDISK_ERROR_MUST_SPECIFY_F_FLAG = 9033
EVDISK_ERROR_SIZE_TOO_LARGE = 9034
EVDISK_ERROR_RESIZE_TOO_LARGE = 9035
EVDISK_ERROR_NO_SUCH_VOLUME = 9036
EVDISK_ERROR_USER_ABORT_ACTION = 9037
EVDISK_ERROR_CLONING = 9038
EVDISK_ERROR_INITIATOR_HAS_VDISK = 9039
EVDISK_ERROR_FILE_IS_SPC_RESERVED = 9040
EVDISK_ERROR_SIZE_TOO_SMALL = 9041
EVDISK_ERROR_SIZE_UNCHANGED = 9042
EVDISK_ERROR_NO_SUCH_SNAPSHOT = 9043
EVDISK_ERROR_IGROUP_NOT_THROTTLED = 9044
EVDISK_ERROR_IGROUP_ALREDY_THROTTLED = 9045
EVDISK_ERROR_THROTTLE_TOO_MUHC = 9046
EVDISK_ERROR_THROTTLE_BEING_DELETED = 9047
EVDISK_ERROR_NO_SUCH_CLONE = 9048
EVDISK_ERROR_NO_ISCSI_THROTTLES = 9049
EVDISK_ERROR_INVALID_ATTR_MODE_VALUE = 9050
EVDISK_ERROR_INITGROUP_MEMBER_CONFLICTING_OS_TYPES = 9051
EVDISK_ERROR_INITGROUP_SET_TYPE_CONFLICT = 9052
EVDISK_ERROR_INITGROUP_MEMBER_VSA_MIXED = 9053
EVDISK_ERROR_INITGROUP_SET_VSA_CONFLICT = 9054
EVDISK_ERROR_RESIZE_FIXES_NOT_GEOM_ALIGNED = 9055
EVDISK_ERROR_RESIZE_VLD_TYPE_LUN_FIXES = 9056
EVDISK_ERROR_RESIZE_IMGAG_TYPE_LUN_FIXES = 9057
EVDISK_ERROR_INITGROUP_F_FLAG_REQUIRED = 9058
EVDISK_ERROR_USE_PARTNER_NOT_APPLICABLE = 9059
EVDISK_ERROR_RESTORE_WALKOVER_EACHOTHER = 9060
EVDISK_ERROR_VOLUME_SPARSE = 9061
EVDISK_ERROR_DESTROY_LUN_BUSY = 9062
EVDISK_ERROR_CANT_CREATE_INITGROUP_FILE = 9063
EVDISK_ERROR_CANT_WRITE_INITGROUP_FILE = 9064
EVDISK_ERROR_CANT_RENAME_INITGROUP_FILE = 9065
EVDISK_ERROR_CANT_CREATE_VFILER_SHADOW_INITGROUP_FILE = 9066
EVDISK_ERROR_CANT_WRITE_VFILER_SHADOW_INITGROUP_FILE = 9067
EVDISK_ERROR_CANT_RENAME_VFILER_SHADOW_INITGROUP_FILE = 9068
EVDISK_ERROR_INITGROUP_TOO_MANY_NODENAMES = 9069
EVDISK_ERROR_LUN_MISSING_FROM_SNAPSHOT = 9070
EVDISK_ERROR_SNAPVALIDATOR_ERROR = 9071
EVDISK_ERROR_PARTNER_HAS_LUN = 9072
EVDISK_ERROR_PARTNER_NOT_REACHABLE = 9073
EVDISK_ERROR_PORTSET_NO_SUCH_SET = 9074
EVDISK_ERROR_PORTSET_ALREADY_EXIST = 9075
EVDISK_ERROR_PORTSET_HAS_PORT = 9076
EVDISK_ERROR_PORTSET_INVALID_PORT_NAME = 9077
EVDISK_ERROR_PORTSET_TOO_MANY_PORTS = 9078
EVDISK_ERROR_PORTSET_WRONG_TYPE = 9079
EVDISK_ERROR_INITGROUP_ALREADY_BOUND = 9080
EVDISK_ERROR_INITGROUP_NOT_BOUND = 9081
EVDISK_ERROR_INITGROUP_EMPTY_PSET_BIND = 9082
EVDISK_ERROR_PORTSET_NO_SUCH_PORT = 9083
EVDISK_ERROR_PORTSET_NO_SUCH_FILER_NAME = 9084
EVDISK_ERROR_PARTNER_HAS_DIFFERENT_OS_TYPE = 9085
EVDISK_ERROR_PARTNER_HAS_DIFFERENT_VSA_SETTING = 9086
EVDISK_ERROR_PORTSET_CANT_CREATE_FILE = 9087
EVDISK_ERROR_PORTSET_CANT_WRITE_FILE = 9088
EVDISK_ERROR_PORTSET_CANT_READ_FILE = 9089
EVDISK_ERROR_PORTSET_CANT_OPEN_FILE = 9090
EVDISK_ERROR_LUN_TOO_LARGE = 9091
EVDISK_ERROR_PORTSET_IC_DOWN = 9092
EVDISK_ERROR_CLONE_NOT_SPLITTING = 9093
EVDISK_ERROR_LUN_HAS_NO_SERIAL_NO = 9095
EVDISK_ERROR_PORTSET_THROTTLE_EXCEEDED = 9096
EVDISK_ERROR_PORTSET_CANT_DESTROY_BOUND_PORTSET = 9097
EVDISK_ERROR_CFMODE_MISMATCH = 9098
EVDISK_ERROR_PORTSET_NOT_VALID_CFMODE = 9099
EVDISK_ERROR_CANNOT_CHANGE_SPCRES_DURING_SPLIT = 9100
EVDISK_ERROR_INITGROUP_BIND_WRONG_TYPE = 9101
EVDISK_ERROR_DB_BAD_INDEX = 9102
EVDISK_ERROR_DB_NO_SUCH_DATABASE = 9103
EVDISK_ERROR_ALUA_NOT_SUPPORTED_ON_ISCSI = 9104
EVDISK_ERROR_ALUA_NOT_SUPPORTED_ON_CFMODE = 9105
EVDISK_ERROR_PORTSET_INVALID_PARTNER_PORT_NAME = 9110
EVDISK_ERROR_PORTSET_BOTH_INVALID_PORT_NAMES = 9111
EVDISK_ERROR_PARTNER_WWNN_MISMATCH_FOR_SSI = 9112
EVDISK_ERROR_INVALID_DEVICE_ID = 9113
EVDISK_ERROR_WWPN_ALIAS_NOT_FOUND = 9114
EVDISK_ERROR_WWPN_ALIASES_NOT_SET = 9115
EVDISK_ERROR_WWPN_ALIASES_TOO_MANY = 9116
EVDISK_ERROR_WWPN_ALIAS_INVALID = 9117
EVDISK_ERROR_QTREE_PRESERVE_FAILED = 9118
EVDISK_ERROR_QTREE_RESTORE_FAILED = 9119
EVDISK_ERROR_QTREE_CLEANUP_FAILED = 9120
EVDISK_ERROR_PREFIX_SUFFIX_SIZE_MISMATCH = 9121
EVDISK_ERROR_ALUA_ISCSI_TRANSPORT_TYPE_CONFLICT = 9122
EVDISK_ERROR_ALUA_FCP_TRANSPORT_TYPE_CONFLICT = 9123
EVDISK_ERROR_LUN_HAS_ALUA_ENABLED_ISCSI_IGROUP = 9124
EVDISK_ERROR_LUN_HAS_ALUA_ENABLED_FCP_IGROUP = 9125
EVDISK_ERROR_LUN_HAS_ISCSI_IGROUP = 9126
EVDISK_ERROR_LUN_HAS_FCP_IGROUP = 9127
EVDISK_ERROR_LUN_HAS_ALUA_CONFLICTS = 9128
EVDISK_ERROR_PORTSET_TOO_FEW_PORTS = 9129
EVDISK_ERROR_WWPN_NOT_FOUND = 9130
EVDISK_ERROR_WWPN_ALIAS_REMOVE_INVALID_NUM_ARGS = 9131
EVDISK_ERROR_IN_TAKEOVER = 9132
EVDISK_ERROR_WWPN_ALIAS_ALREADY_SET = 9133
EVDISK_ERROR_VOLUMES_ONLINING = 9134
EVDISK_ERROR_VIRTUAL_LUN_MAPPING_CONFLICT = 9140
EVDISK_ERROR_LUN_STREAM_DATAUNRECOVERABLE = 9144
EVDISK_ERROR_VDISK_NOT_STOPPED = 9146
EVDISK_ERROR_INVALID_PREFIX_SIZE = 9147
EVDISK_ERROR_INVALID_SUFFIX_SIZE = 9148
EAPIERROR = 13001
EAPIAUTHENTICATION = 13002
EAPIPRIVILEDGE = 13003
EAPIPRIVILEGE = 13003
EAPIEXCEPTION = 13004
EAPINOTFOUND = 13005
EAPIMISSINGARGUMENT = 13006
EAPINOTIMPLEMENTED = 13007
EAPILICENSE = 13008
EAPIINDEXTOOLARGE = 13009
EAPIUNSUPPORTEDVERSION = 13010
EAPITRANSMISSION = 13011
EOPNOTSUPPORTED = 13012
EALREADYSTARTED = 13013
ENOTSTARTED = 13014
ESERVICENOTSTOPPED = 13015
ENOTWHILEWAITINGFORGIVEBACK = 13016
ENOTINMAINTMODE = 13017
ENOTINREADONLYMODE = 13018
EAPITOOMANYENTRIES = 13019
ESNAPSHOTEXISTS = 13020
ESNAPSHOTDOESNOTEXIST = 13021
ESNAPSHOTTOOMANY = 13022
ESNAPSHOTNOTALLOWED = 13023
ESNAPSHOTBUSY = 13024
ESNAPSHOTNOSPACE = 13025
EDUPLICATEDSID = 13026
EINVALIDDSID = 13027
EINVALIDMSID = 13028
EAMBIGUOUS_DSID = 13029
ESNAPSHOT_NOT_LATEST = 13030
ESTRIPEDRESTOREOPNOTFOUND = 13037
EVOLUMESNAPRESTOREERROR = 13038
EVOLUMEQUIESCED = 13039
EVOLUMEDOESNOTEXIST = 13040
EVOLUMEMOUNTING = 13041
EVOLUMEOFFLINE = 13042
EVOLUMEREADONLY = 13043
EVOLUMENAMEINVALID = 13044
EVOLUMERGSIZEINVALID = 13045
EVOLUMELANGUAGEINVALID = 13046
EVOLUMEDISKSIZEINVALID = 13047
EVOLUMEDISKDUP = 13048
EVOLUMERGINVALID = 13049
EQUOTAPARSEERROR = 13050
EQUOTAINVALID = 13051
EQUOTAEXISTS = 13052
EQUOTADOESNOTEXIST = 13053
EQUOTADIRECTIVE = 13054
EAPI_CONNECTION = 13055
EAPI_CONNECTION_DROPPED = 13056
EAPI_RECEPTION = 13057
EVOL_NOT_OFFLINE = 13058
EVOL_NOT_RESTRICTED = 13059
EVOL_ONLINE = 13060
EVOL_RESTRICTED = 13061
EVOL_SPACE_FOR_GUARANTEE = 13062
EVOL_TOO_MANY = 13063
EVOLUME_NOT_QUIESCED = 13064
EVOLUME_CLEAR_QUIESCE = 13065
EVOLUME_ALREADY_QUIESCED_SET = 13066
EVOLUME_ALREADY_QUIESCED_CLEAR = 13067
EVOL_CIFS_OPENS = 13068
EVOL_INVALID_FSINFO = 13069
EVFILEROPNOTALLOWED = 13070
EVFILERNOTFOUND = 13071
EVFILEROPNOTCOMPLETED = 13072
EIPSPACENOTFOUND = 13073
EVOL_UNKNOWN_VERSION = 13074
EVOL_CIFS_ENABLED = 13075
EQTREEEXISTS = 13080
EQTREENOTOWNER = 13081
EQTREEMAX = 13082
ECMSINVALIDREQUEST = 13090
ECMSNOTENABLED = 13091
ECMSPROCESSINGERROR = 13092
ESNAPMIRROROFF = 13100
ESNAPMIRRORPARSERERROR = 13101
ESNAPMIRRORERROR = 13102
EISCSISECINVALIDAUTHTYPE = 13109
EISCSISECINVALIDINPUTERROR = 13110
EISCSISECPROCESSINGERROR = 13111
EISCSISECINITNOTFOUNDERROR = 13112
EFILENOTFOUND = 13113
EINTERNALERROR = 13114
EINVALIDINPUTERROR = 13115
ESETSPCRESERROR = 13116
EADAPTERNOTFOUND = 13122
EADAPTERPARTNER = 13123
EADAPTERINVALIDTYPE = 13125
ENOADAPTERPARTNER = 13126
ENOVIRTUALADAPTERS = 13127
ENOTCLUSTERED = 13128
ECLUSTERED = 13129
EDISKNOTFOUND = 13150
ESWAPINPROGRESS = 13151
ENOTDISKOWNER = 13152
EDISKINRAIDZEROVOL = 13153
EDISKISSPARE = 13154
EVOLUMEPLEXINVALID = 13155
EVOLUMEINUSE = 13156
EVOLUMENOTONLINE = 13157
EVOLUMEBUSY = 13158
EVOLUMECIFSTERMINATE = 13159
EVOLUMECREATING = 13160
ECLIENTSTATSVFILER = 13161
ECLIENTSTATSNOTENABLED = 13162
ENOACTIVECLIENTS = 13163
ECIFSNOTCONFIGURED = 13164
EDNSNOTENABLED = 13165
EHOSTNOTFOUND = 13166
ELDAPSVRNOTFOUND = 13167
EVOL_ONLINE_ERROR = 13168
EVOL_PARTIAL = 13169
EVOLNOTCLONE = 13170
EVOLOPNOTUNDERWAY = 13171
EVOLUME_NOT_QUIESCED_MISSING_PARAMS = 13172
EVOLUME_NOT_QUIESCED_NOMORE_SNAPSHOTS = 13173
EVOLUME_NOT_QUIESCED_SNAP_CREATE_BUSY = 13174
EVOLUME_NOT_QUIESCED_TIMEDOUT = 13175
EVOLUME_NOT_QUIESCED_PENDING_VOL_REFS = 13176
EVOLUME_NOT_QUIESECED_PENDING_SNAP_REFS = 13177
EVOLUME_NOT_QUIESCED_PENDING_MSGS = 13178
EVOLUME_NOT_QUIESCED_CP_SYNC_TIMEDOUT = 13179
EVOLUME_NOT_QUIESCED_SNAPSHOT_EXISTS = 13180
EVOLUME_NOT_QUIESCED_SNAP_SCHED_ABORT_TIMEDOUT = 13181
EVOLUME_NOT_QUIESCED_ZOMBIE_DRAIN_TIMEDOUT = 13182
EVOLUME_NOT_QUIESCED_SNAP_CREATE_TIMEDOUT = 13183
EVOLUME_NOT_QUIESCED_CLONE_FROM_SNAPSHOT_EXISTS = 13184
EVOLUME_NOT_QUIESCED_CANT_CREATE_SNAPSHOT = 13185
EVOLUME_NOT_QUIESCED_CANT_CREATE_SNAPSHOT_NO_SPACE = 13186
ESVCDISABLED = 13200
ESVCNOTAVAIL = 13201
ESHAREACCESSDENIED = 13202
ESHAREEXISTS = 13203
ESHARETOOMANY = 13204
ECIFSSHARINGVIOLATION = 13210
ESANOWNNOTENABLED = 13210
EINVALIDHOST = 13211
EINVALIDOWNERID = 13212
EINVALIDOWNER = 13213
EINVALIDPASSWORD = 13214
EEXPORTSINCOMPATIBLE = 13215
EINODENUMBERTOOSMALL = 13216
EINODENUMBERTOOLARGE = 13217
EINVALIDINODE = 13218
EINELIGIBLEINODE = 13219
EPARENTINFONOTLOADED = 13220
EI2PNOTENABLED = 13221
EVV_COMMON = 13222
ECIFS_LOGIN_FAILED = 13250
ECIFS_BIND_FAILED = 13251
ECIFS_DNS_REQUIRED = 13252
ECIFS_KRB_CONFLICT = 13253
ECIFS_AD_CLOCK_SKEW = 13254
ECIFS_AD_RESET_REQUIRED = 13255
ECIFS_LIST_UNAVAILABLE = 13256
ECIFS_DC_CONNECT_FAILED = 13257
ECIFS_HAVE_SESSION_SCOPED_LOCKS = 13258
ECIFS_PASSWD_AND_GROUP_REQUIRED = 13259
ECIFS_SETUP_CANNOT_WRITE = 13260
EEMS_INVOKE_FAILED = 13301
EEMS_INVOKE_BAD_PARAM = 13303
EEMS_INVOKE_ID_BAD = 13310
EEMS_INVOKE_SEVERITY_REQUIRED = 13311
EEMS_INVOKE_SEVERITY_INVALID = 13312
EEMS_INVOKE_SEVERITY_NOT_VARIABLE = 13313
EEMS_INVOKE_PARAMS_INSUFFICIENT = 13314
EEMS_INVOKE_VERSION_INVALID = 13315
EEMS_INVOKE_SUPRESS_DUP = 13316
EEMS_INVOKE_SUPRESS_TIMER = 13317
EEMS_INVOKE_NVRAM_TOO_BIG = 13318
EEMS_INVOKE_QUEUE_FULL = 13319
EREALLOCATE_EXISTS = 13501
EREALLOCATE_BADPATH = 13502
EREALLOCATE_NOMEM = 13503
EREALLOCATE_NOSCAN = 13504
EREALLOCATE_BADVOL = 13505
EREALLOCATE_READONLY = 13506
EREALLOCATE_BADSCHED = 13507
EREALLOCATE_OFF = 13508
EREALLOCATE_SNAPSHOT = 13509
EDISKNOTSPARE = 13510
EDISKTOOSMALL = 13511
ERAIDGROUPDEGRADED = 13512
ESAVECOREDISK = 13513
EINVALIDSTATE = 13514
ECANT_USE_ALL_DISKS = 13515
ENPMINVPLOC = 13600
ENPMNOPKG = 13601
ENPMNOMETA = 13602
ENPMERXMETA = 13603
EINCRCOPYFAILED = 13604
EINCRCOPYOPNOTFOUND = 13605
EINCRCOPYINVALIDUUID = 13606
EINCRCOPYINVALIDOP = 13607
EINCRCOPYNOMEM = 13608
EINCRCOPYINVALIDINPUT = 13609
EINCRCOPYINVALIDOPTYPE = 13610
EINCRCOPYDUPLICATESESSION = 13611
EINCRCOPYNOTSUPPORT = 13612
EINCRCOPYVOLOFFLINE = 13613
EINCRCOPYVOLNOTFOUND = 13614
EINCRCOPYSNAPCREATIONFAIL = 13615
EINCRCOPYSNAPSHOTEXIST = 13616
EINCRCOPYNOSTREAMESTABLISHED = 13617
EINCRCOPYAGAIN = 13618
EINCRCOPY_CSM_CALL_FAIL = 13619
EINCRCOPY_CSM_SEND_FAIL = 13620
EINCRCOPY_CSM_CANT_GET_SESSION = 13621
EINCRCOPY_CSM_CANT_REGISTER_SENDCB = 13622
EDSIDPARSEERROR = 13623
EINCRCOPY_SET_INCORE_QUIESCE_VOL_FAIL = 13624
EINCRCOPY_UNSET_INCORE_QUIESCE_VOL_FAIL = 13625
EINCRCOPY_SET_ONDISK_QUIESCE_VOL_FAIL = 13626
EVOLMOVE_NDMP_DUMPS_RUNNING = 13627
EINCRCOPY_DUMPS_RUNNING = 13627
EVOLMOVE_NDMP_RESTORE_RUNNING = 13628
EINCRCOPY_RESTORE_RUNNING = 13628
EVOLMOVE_SIS_UNDO_RUNNING = 13629
EVOLMOVE_WAFL_ERR = 13630
EVOLMOVE_AGENT_IS_INITIALIZING = 13631
EVOLMOVE_LOCKED_FOR_SNAPMIRROR = 13632
ECGERROR = 13700
ECGSNAPERR = 13701
ECGOFF = 13702
ECHARMAP_INVALID = 13800
ECHARMAP_NO_PERSIST = 13801
ETOERRMIN = 13900
ESERVICENOTINITIALIZED = 13901
ESERVICENOTLICENSED = 13902
ESERVICENOTENABLED = 13903
EMBOXDEGRADED = 13904
EMBOXUNKNOWN = 13905
EMBOXVERSIONMISMATCH = 13906
EPARTNERDISABLEDTO = 13907
EOPERATORDENY = 13908
ENVRAMSIZEMISMATCH = 13909
EVERSIONMISMATCH = 13910
EINTERCONNECTERROR = 13911
EPARTNERBOOTING = 13912
ESHELFHOT = 13913
EPARTNERREVERT = 13914
ELOCALREVERT = 13915
EPARTNERTRYINGTAKEOVER = 13916
ETAKEOVERINPROGRESS = 13917
EHALTNOTAKEOVER = 13918
EUNSYNCNVRAM = 13919
EUNKNOWNTAKEOVERERROR = 13920
EWAITINGFORPARTNER = 13921
ELOWMEMORY = 13922
EHALTING = 13923
EMBOXUNCERTAIN = 13924
ENOAUTOTAKEOVER = 13925
EPARTNERNOTWAITING = 13926
ENOAGGRS = 13927
EOP_DISALLOWED_DURING_GIVEBACK = 13928
EOP_DISALLOWED_BRINGING_OFFLINE = 13929
EOP_DISALLOWED_BRINGING_ONLINE = 13930
EOP_DISALLOWED_DURING_DESTROY = 13931
EOP_DISALLOWED_VOLUME_FENCED = 13932
EOP_DISALLOWED_VOLUME_FROZEN = 13933
EOP_DISALLOWED_VOLUME_OLDLABELS = 13934
EOP_DISALLOWED_VOLUME_NEEDED_LAZY_SPCRSRV = 13936
ENOPARTNERINVENTORY = 13937
EPARTNERMISSINGDISKS = 13938
ENOTHINGTOTAKEOVER = 13945
ESENDHOMEINPROGRESS = 13946
ENVRAMDOWN = 13947
EINTERCONNECTRESET = 13948
EBADOPTIONS = 13949
ENOTHALTED = 13950
EREVERTINPROGRESS = 13951
ESERVICEENABLED = 13952
EINTAKEOVER = 13953
ETOERRMAX = 13954
EOPLOCKRECALLFAILED = 13955
EOP_DISALLOWED_DURING_REVERT = 13956
EVOLUME_ADMINOP_NOT_FENCED = 13957
EINVALIDRESERVATION = 14000
ENODISKSFOUND = 14001
EMUSTBEINMAINTMODE = 14002
EFILEEXISTS = 14003
EJUNCTIONEXISTS = 14004
EJUNCTIONDOESNOTEXIST = 14005
EBADFILELENGTH = 14006
EFILER_NOT_HEALTHY = 14007
EBADCOREID = 14100
ECOREDUMPBUSY = 14101
ECOREDUMPNOTINITIALIZED = 14102
ESESNOTREADY = 14200
ESESBUSY = 14201
ERDB_HA_SF_NOT_INITIALIZED = 14300
ERDB_HA_ID_MISMATCH = 14301
ERDB_HA_CONFIGURED = 14302
ERDB_HA_PARTIALLY_CONFIGURED = 14303
ERDB_HA_NOT_CONFIGURED = 14304
ERDB_HA_CONFIG_UUID_MISMATCH = 14305
ERDB_HA_CANNOT_EXIT_CONFIG = 14306
ERDB_HA_IO_ERROR = 14307
ERDB_HA_INVALID_SLOT = 14308
ERDB_HA_OLD_COOKIE = 14309
ERDB_HA_INVALID_INPUT = 14310
ERDB_HA_FAILURE = 14311
ERDB_HA_ILLEGAL_SLOT_CONTENT = 14312
ERDB_HA_SLOT_UUID_MISMATCH = 14313
ERDB_HA_QUIESCENT_PERIOD = 14314
EFIJIINVALID = 14401
EFIJIINVALIDEXPR = 14402
EFIJINOFILTER = 14403
EFIJIMAXFILTERS = 14404
EAGGRDOESNOTEXIST = 14420
EAGGRNOTONLINE = 14421
EAGGRFAILINGOVER = 14422
EAGGRMISMATCH = 14423
ENFS_CLIENT_STATS_NOT_ENABLED = 14424
ELOOPUNAVAILABLE = 14425
ESNAPSHOTEXISTSPARTIAL = 14426
ESNAPVAULTERR = 14450
ESNAPVAULTSETUP = 14451
ESNAPVAULTRESOURCE = 14452
ESNAPVAULTBUSY = 14453
EVOLUME_NOT_QUIESCED_NOT_MOUNTED = 14460
EVOLUME_NOT_QUIESCED_ROOT_VOLUME = 14461
EVOLUME_NOT_QUIESCED_NOT_FLEX = 14462
EVOLUME_NOT_QUIESCED_IRONING = 14463
EVOLUME_NOT_QUIESCED_GOING_HOME = 14464
EVOLUME_NOT_QUIESCED_CB_TIMEOUT = 14465
EVOLUME_NOT_QUIESCED_NOT_DRAIN = 14466
EVOLUME_NOT_QUIESCED_FOR_CORAL = 14467
EVOLAGGRISIRONING = 14468
EVOLUME_HAS_VFILER_STORAGE = 14469
EVOLUME_QUIESCING = 14470
EVOLUME_NOT_BOOLEAN_VALUE = 14471
EVOLUME_TYPE_NOT_SUPPORTED = 14472
EVOLISGRIDIRONING = 14473
EONTAPI_ESNAPDIFF_FILENAME_UNAVAILABLE = 14474
EVOLUME_NOT_QUIESCED_SAN_NOTIFICATION_TIMEOUT = 14475
EONTAPI_ESNAPDIFF_FILETYPE_MODIFIED = 14476
ELOGROTATIONACTIVE = 14499
ESNAPDIFFINTERROR = 14500
ESNAPDIFFINVINPUT = 14501
ESNAPDIFFINVSNAPSHOT = 14502
ESNAPDIFFSNAPSHOTCHANGED = 14503
ESNAPDIFFSNAPSHOTEARLIER = 14504
ESNAPDIFFMAXSESSIONSEXCEEDED = 14506
ESNAPDIFFDUPLICATESESSION = 14507
ESNAPDIFFINVALIDSESSION = 14508
ESNAPDIFFNOI2P = 14509
ESNAPDIFFVOLOFFLINE = 14510
ESNAPDIFFABORTED = 14511
EVOLUMEGSMINVALID = 14512
EAPIMISSINGOUTPUT = 14513
EINVALIDOUTPUTERROR = 14514
EVOLUMECOMPRESSED = 14515
EVOLUMENOTDECOMPRESSING = 14516
ENOTIMEZONESET = 14517
ENOTIMEZONEVERSION = 14518
EINVALIDTIMEZONE = 14519
ETIMEZONEDIFFERENTINRC = 14520
ESNAPLOCKNOTLICENSED = 14521
ECOMPLIANCECLOCKNOTSET = 14522
ETAKENOVER = 14523
EDATENOTSETONPARTNER = 14524
ERSHSESSIONERROR = 14525
ERSHKILLERROR = 14526
EDENSE_REVERTING = 14527
EDENSE_IRON_RUNNING = 14528
EDENSE_CLONE_SFSR_INPROG = 14529
EDENSE_NLCSR_INPROG = 14530
EDENSE_VOL_NONEXIST = 14531
EDENSE_VOL_OFFLINE = 14532
EDENSE_VOL_NOTSUP = 14533
EDENSE_VOL_RDONLY = 14534
EDENSE_VOL_TRANSITING = 14535
EDENSE_VOL_RESTRICTED = 14536
EDENSE_SNAPSHOT_CREATE = 14537
EDENSE_SNAPSHOT_DELETE = 14538
EDENSE_SNAPSHOT_NONEXIST = 14539
EDENSE_STALE_DINODE = 14540
EDENSE_STALE_RINODE = 14541
EDENSE_STALE_DBUF = 14542
EDENSE_STALE_RBUF = 14543
EDENSE_CIFS_HOLE_RERVD = 14544
EDENSE_DONOR_TOO_SMALL = 14545
EDENSE_RECIPIENT_TOO_SMALL = 14546
EDENSE_NO_SPACE = 14547
EDENSE_SHUTDOWN = 14548
EDENSE_FAILOVER = 14549
EDENSE_DONOR_RANGE = 14550
EDENSE_RECPT_RANGE = 14551
EDENSE_QUOTA_CHECK = 14552
EDENSE_UNSUPPORTED_VOLTYPE = 14553
EDENSE_CLONE_SPLITTING = 14554
EDENSE_CLONE_STOPPED = 14555
EDENSE_CLONE_SFILE_NONEXIST = 14556
EDENSE_CLONE_CFILE_NONEXIST = 14557
EDENSE_CLONE_NO_SLOT = 14558
EDENSE_CLONE_NO_ARGS = 14559
EDENSE_CLONE_DIFF_VOLUME = 14560
EDENSE_CLONE_SAME_FILE = 14561
EDENSE_CLONE_VOL_REVERTING = 14562
EDENSE_CLONE_IN_PROG = 14563
EDENSE_CLONE_SNAPNAME = 14564
EDENSE_CLONE_SNAPPATH = 14565
EDENSE_CLONE_SNAP_FH = 14566
EDENSE_CLONE_SNAP_ATTR = 14567
EDENSE_CLONE_SFILE_ATTR = 14568
EDENSE_CLONE_CFILE_ATTR = 14569
EDENSE_CLONE_EXIST = 14570
EDENSE_CLONE_METAFILE = 14571
EDENSE_CLONE_METAFILE_FH = 14572
EDENSE_CLONE_METAFILE_WRITE = 14573
EDENSE_CLONE_METAFILE_ATTR = 14574
EDENSE_CLONE_METAFILE_READ = 14575
EDENSE_CLONE_SFILE_READ = 14576
EDENSE_CLONE_CFILE_WRITE = 14577
EDENSE_CLONE_FH = 14578
EDENSE_CLONE_CREATE = 14579
EDENSE_CLONE_SETATTR = 14580
EDENSE_CLONE_SOURCE_FH = 14581
EDENSE_CLONE_NOT_SUPP = 14582
EDENSE_CLONE_PROC = 14583
EDENSE_CLONE_TYPE_SUPP = 14584
EDENSE_CLONE_SRC_OUTOF_RANGE = 14585
EDENSE_CLONE_DEST_OUTOF_RANGE = 14586
EDENSE_CLONE_OVERLAP_RANGE = 14587
EDENSE_CLONE_INVALID_RANGE = 14588
EDENSE_CLONE_RUNNING_OP = 14589
EDENSE_CLONE_NOT_RUNNING = 14590
EDENSE_CLONE_NO_OP = 14591
EDENSE_CLONE_NOT_FAILED = 14592
EDENSE_CLONE_DEL_INFO = 14593
EDENSE_CLONE_PENDING_SNAP = 14594
EDENSE_CLONE_SPLIT_MAP = 14595
EDENSE_CLONE_INVALID_SOURCE = 14596
EDENSE_CLONE_INVALID_CLONE = 14597
EDENSE_CLONE_SNAP_DEL = 14598
EDENSE_CLONE_GET_SNAPID = 14599
EDENSE_CLONE_SMALL_DATA = 14600
EDENSE_VDISK_INVALID_NAME = 14601
EDENSE_VDISK_NOT_IN_QTREE_ROOT = 14602
EDENSE_VDISK_VOL_SPARSE_WO_SCSI = 14603
EDENSE_VDISK_INTERNAL_ERROR = 14604
EDENSE_VDISK_INVALID_FH = 14605
EDENSE_VDISK_NO_SUCH_VDISK = 14606
EDENSE_VDISK_LBA_OFFSET_MISALIGNED = 14607
EDENSE_VDISK_SRC_INVALID_BLOCK_RANGE = 14608
EDENSE_VDISK_DST_INVALID_BLOCK_RANGE = 14609
EDENSE_VDISK_SRC_LUN_CLONE = 14610
EDENSE_CLONE_MAX_OPS_VOL = 14611
EDENSE_CLONE_INVALID_DIR = 14612
EDENSE_CLONE_NOT_QTREE_ROOT = 14613
EDENSE_CLONE_LARGE_INFO = 14614
EDENSE_CLONE_INVALID_ID = 14615
EDENSE_CLONE_NOT_LICENSED = 14616
EDENSE_CLONE_LICENSE_EXPIRED = 14617
EDENSE_CLONE_FILE_FOLD_INPROG = 14618
EDENSE_CLONE_WORM_VOL = 14619
EDENSE_CLONE_INVALID_UUID = 14620
EDENSE_CLONE_EXISTING_OP = 14621
EDENSE_CLONE_CHANGELOG_OFF = 14622
EDENSE_NON_SUPPORTED_PLATFORM = 14623
EDENSE_STALE_CLONE_DIR_INODE = 14624
EDENSE_CLONE_DIR_FH = 14625
EDENSE_CLONE_MAX_OPS_FILER = 14626
EDENSE_CLONE_METAFILE_VER_MISMATCH = 14627
EDENSE_UNKNOWN = 14628
EROUTEEXISTS = 14629
EINVALIDROUTE = 14630
EROUTENOTFOUND = 14631
EVLANEXISTS = 14632
EINVALIDTAG = 14633
EINTERFACENOTFOUND = 14634
EIPSPACEEXISTS = 14635
EIPSPACEDOESNOTEXIST = 14636
EDENSE_CLONE_MAX_OPS_VFILER = 14637
EDENSE_CLONE_SRC_VFACCESS = 14638
EDENSE_CLONE_DST_VFACCESS = 14639
EDENSE_CLONE_VFILER_NOT_RUNNING = 14640
EDENSE_VFILER_CUTOVER = 14641
EDISKTYPEWRONGFORSNAPLOCK = 14700
EDISKTYPEWRONGFORVOL = 14701
EDISK_TYPE_MISMATCH = 14702
EVOL_ALREADY_MOUNTED = 14713
EVOL_MOUNT_FAILED = 14714
EJUNCTION_CREATE_FAILED = 14715
EVOL_NOT_MOUNTED = 14716
EVOL_UNMOUNT_FAILED = 14717
EJUNCTION_DELETE_FAILED = 14718
EVSERVER_OP_NOT_ALLOWED = 14719
EDENSE_COMP_SCAN_ACTIVE = 14900
EDENSE_CLONE_SUB_COMPRESSION = 14901
EDENSE_CLONE_DECOMP_ACTIVE = 14902
EINVALIDPATH = 14920
EVSERVERNAMEEXISTS = 14922
EVSERVERALREADYSTARTED = 14923
EVSERVERNOTRUNNING = 14924
ESIS_CLONE_VOL_NONEXIST = 14925
ESIS_CLONE_VOL_OFFLINE = 14926
ESIS_CLONE_VOL_NOTSUP = 14927
ESIS_CLONE_VOL_RDONLY = 14928
ESIS_CLONE_VOL_TRANSITING = 14929
ESIS_CLONE_STALE_INODE = 14930
ESIS_CLONE_STALE_DINODE = 14931
ESIS_CLONE_STALE_RINODE = 14932
ESIS_CLONE_SHUTDOWN = 14933
ESIS_CLONE_FAILOVER = 14934
ESIS_CLONE_CLONE_SFILE_NONEXIST = 14935
EVOL_NFS_ENABLED = 14936
ESIS_CLONE_CLONE_DIFF_VOLUME = 14937
ESIS_CLONE_CLONE_SFILE_ATTR = 14938
ESIS_CLONE_CLONE_CFILE_ATTR = 14939
ESIS_CLONE_CLONE_FH = 14940
ESIS_CLONE_CLONE_SOURCE_FH = 14941
ESIS_CLONE_CLONE_TYPE_SUPP = 14942
ESIS_CLONE_NLCSR_INPROG = 14943
ESIS_CLONE_CLONE_OVERLAP_RANGE = 14945
ESIS_CLONE_CLONE_INVALID_RANGE = 14946
ESIS_CLONE_CLONE_INVALID_SOURCE = 14947
ESIS_CLONE_CLONE_INVALID_CLONE = 14948
ESIS_CLONE_CLONE_INVALID_DIR = 14949
ESIS_CLONE_CLONE_WORM_VOL = 14950
ESIS_CLONE_VDISK_INVALID_NAME = 14951
ESIS_CLONE_CLONE_EXIST = 14952
ESIS_CLONE_SFILE_READ = 14953
ESIS_CLONE_CFILE_WRITE = 14954
ESIS_CLONE_LICENSE_EXPIRED = 14955
ESIS_CLONE_NOT_LICENSED = 14956
EVOL_IN_NVFAILED_STATE = 14957
EQUOTAS_NO_VALID_RULES = 14958
EQUOTA_POLICY_NOT_FOUND = 14959
ESIS_CLONE_DECOMP_ACTIVE = 14960
ESIS_CLONE_SPLIT_MAP = 14961
ESIS_CLONE_SOURCE_TOO_SMALL = 14962
ESIS_CLONE_DOWNGRADE = 14963
ESIS_CLONE_FLEXCLONE_SPLITTING = 14964
ESIS_CLONE_CLONE_INVALID_SPC_RSRV = 14965
ESIS_CLONE_UNKNOWN = 14966
ESIS_CLONE_MAX_RANGES = 14967
ESIS_CLONE_MAX_BLKS = 14968
ESIS_CLONE_CLONE_CFILE_NONEXIST = 14970
ESNAPMIRROR_NOT_INITIALIZED = 15000
EAGGR_TOO_LARGE = 15001
EQTREE_SECURITY_GET_FAILED = 15002
EQTREE_OPLOCK_GET_FAILED = 15003
EINTENTLOG_READ_FAILED = 15004
EOPLOCKS_TOO_MANY_RECALLS_PENDING = 15007
ESNAPMIRRORSUBSYSTEMNOTINITED = 15008
EQUOTA_CONTROL_METAFILE_OPEN = 15009
EQUOTA_CONTROL_METAFILE_READ = 15010
EMAXFILES_TOO_LARGE = 15011
ESNAPMIRRORDESTSTATEINVALID = 15012
EILLEGAL_INODE_CHECK = 15013
ECOL_COPY_INVALIDINPUTERROR = 15014
ECOL_COPY_INTERNALERROR = 15015
ECOL_COPY_FILENOTFOUND = 15016
ECOL_COPY_NORESOURCES = 15017
ECOL_COPY_NOACCESSTOSRC = 15018
ECOL_COPY_VOLOFFLINE = 15019
ECOL_COPY_DSTREADONLY = 15021
ECOL_COPY_ISDIRECTORY = 15022
ECOL_COPY_NOSPACE = 15023
ECOL_COPY_COPYFAILED = 15024
ECOL_STATUS_INVALIDINPUTERROR = 15025
ECOL_STATUS_COPYIDNOTFOUND = 15026
ECOL_STATUS_INTERNALERROR = 15027
ECOL_ABORT_INVALIDINPUTERROR = 15029
ECOL_ABORT_INTERNALERROR = 15030
ECOL_ABORT_COPYIDNOTFOUND = 15031
ETELNETSHUTDOWNERROR = 15032
ECORALSET_ONLINE_FAILED = 15550
ESTRIPEDVOL_NOT_FULLY_ONLINE = 15551
EVOL_BAD_VVLABEL_CKSUM = 15600
EVOL_BAD_VVLABEL_MAGIC = 15601
EVOL_BAD_VVLABEL_UUID = 15602
EVOL_BAD_VVLABEL_VERSION = 15603
EVOL_FAILED_TO_ONLINE = 15604
EVOL_INCOMPLETE = 15605
EVOL_MIRROR_TYPE_INVALID = 15606
EVOL_BAD_MODE_BITS = 15607
ECOMPRESSING = 15608
EVOLUMENOTCOMPRESSENABLED = 15609
ECOMPRESSIONGATHERER = 15610
ECOMPSHARINGBEYONDLIMIT = 15611
ECOMPRESSCLONEINPROG = 15612
EIRON_STREAM_DIR_UPGRADE = 15650
EIRON_UPGRADE_DISALLOWED = 15651
EIRON_NOT_RUNNING = 15652
EIRON_OC_DISALLOWED = 15653
EIRON_PREV_CP_DISALLOWED = 15654
EIRON_QTREE_READONLY = 15655
EIRON_ROOT_AGGR_DISALLOWED = 15656
EIRON_SCANS_DISALLOWED = 15657
EIRON_SPARSE_VOL_NOT_ONLINE = 15658
EIRON_STARTING = 15659
EIRON_STOP_IN_PROGRESS = 15660
EOBJECTNOTFOUND = 15661
ESNAPMIRRORTRANSFERFAILED = 15662
ESNAPMIRRORINVALIDUUID = 15663
ESNAPMIRRORINVALIDINPUT = 15664
ESNAPMIRRORNOMEM = 15665
ESNAPMIRRORNOTSUPPORT = 15666
ESNAPMIRRORVOLNOTFOUND = 15667
ESNAPMIRROROPNOTFOUND = 15668
EQTREE_DOES_NOT_EXIST = 15669
EQTREE_HAS_SHARES = 15670
EQTREE_HAS_FILES = 15671
EQUOTAS_ON = 15672
EQUOTAS_OFF = 15673
EOP_DISALLOWED_ON_NOT_HOME_AGGR = 15674
EOP_DISALLOWED_ON_ROOT_AGGR = 15675
EOP_DISALLOWED_ON_AGGR_WITH_NODE_VOLS = 15676
EOP_DISALLOWED_ON_STRIPED_AGGR = 15677
EINVALID_HA_POLICY = 15678
ESTAMPREDIRECTSNAPIDERROR = 15679
EQUOTAS_OPERATION_MISMATCH = 15680
EVOLUME_OP_NOT_SUPPORTED_BY_OWNER = 15681
EOP_ERR_MODE_MISMATCH_OBJ_ORIGINALLY_CLUSTERED = 15682
EOP_ERR_MODE_MISMATCH_OBJ_ORIGINALLY_UNCLUSTERED = 15683
EOP_CLUSTER_ATTR_DISALLOWED = 15684
ESNAPMIRRORTRANSFEREXISTS = 15685
ESNAPMIRRORCHECKMISMATCH = 15686
ESNAPMIRRORIMAGENOTFOUND = 15687
ESNAPMIRRORSTREAMNOTFOUND = 15688
ESNAPMIRRORTRANSFERNOTFOUND = 15689
ESNAPMIRRORSESSIONNOTFOUND = 15690
ESNAPMIRRORTRANSFERNOTCOMPLETE = 15691
ESNAPMIRRORINTERNALERROR = 15692
ESNAPMIRROROTHER = 15693
EARRAYNOTFOUND = 15694
EOP_DISALLOWED_ON_CFO_AGGR = 15695
EOP_DISALLOWED_ON_SFO_AGGR = 15696
ENODENOTFOUND = 15697
EVSERVERNOTFOUND = 15698
EUSECLUSTERNATIVEUI = 15699
ESCHEDNOTFOUND = 15700
EMULTIPLEVOLSFOUND = 15701
EVERSION_INVALIDRANGE = 15702
EVERSION_EXISTS = 15703
ERESOURCEINUSE = 15704
EVOL_MANIFEST_NOT_AVAILABLE = 15705
EVOL_MANIFEST_QUERY_NOT_DEFINITIVE = 15706
EVOL_TRANS_BLOCKING_FEATURES = 15707
EUNABLE_TO_UPDATE_VOLDB = 15708
EVOL_UNABLE_TO_SET_UP_SNAPSHOT_XLATE_TABLE = 15709
EAGGR_SNAPSHOT_IN_PROGRESS = 15710
EAGGR_HAS_SNAPSHOTS = 15711
EAGGR_HAS_UNSUPPORTED_VOLUME = 15712
EAGGR_CANT_UNDO_HYBRID = 15713
EAGGR_HYBRID = 15714
EOP_DISALLOWED_ON_SSD_AGGR = 15715
ENOT_A_AZCS_DISK = 15716
ENO_AZCS_DISKS = 15717
EMCS_NOT_ALLOWED_WITH_LUNS = 15718
EAGGR_ZONED_NOT_ALLOWED_WITH_DISKS = 15719
ESNAPSHOTRESTOREINPROGRESS = 15801
ESNAPSHOTTAGSERR = 15802
ESNAPSHOTINVALIDID = 15803
ESNAPSHOTTAGSNOSPACE = 15804
ESNAPSHOTTAGSMETAFILEERR = 15805
EVOL_NOT_IRON_RESTRICTED = 15850
EIRON_NOT_OPTCOMMIT = 15851
EVOL_HAS_REPLICA = 15852
EDENSE_VOL_COMPRESSED = 15853
EDENSE_CG_MISMATCH = 15854
EMULTIPLEOPTSFOUND = 15855
EVOLUME_64BIT_UPGRADE_MODE_INVALID = 15856
EAGGR_WOULD_UPGRADE = 15857
EAGGR_64BIT_UPGRADE_NOT_IN_PROGRESS = 15858
EAGGR_SIZE_LESS_THAN_16TB = 15859
EAGGR_64BIT_UPGRADE_ENOSPC = 15860
EVOLUME_64BIT_UPGRADE_VVOL_ENOSPC = 15861
EAGGR_64BIT_UPGRADE_RESTRICTED = 15862
EOP_DISALLOWED_ON_TRAD = 15863
EVOLUME_ALREADY_64BIT = 15864
EVOLUME_64BIT_UPGRADE_DISALLOWED = 15865
EVOLUME_CANT_OBTAIN_VOLREF = 15866
EVOLUME_64BIT_UPGRADE_KIREETI_NOT_AVAIL = 15867
EVOLUME_64BIT_UPGRADE_PREQUAL_NOT_AVAIL = 15868
EVOLUME_64BIT_UPGRADE_ESTIMATE_IN_PROGRESS = 15869
EONTAPI_VOLTRANS_JOBNOTFOUND = 15870
EONTAPI_VOLTRANS_LOG_INVALIDOFFSET = 15871
EONTAPI_VOLTRANS_LOG_REC_NOTFOUND = 15872
EDENSE_DEDUPE_NOT_DISABLED = 15873
EDENSE_COMPRESSION_NOT_DISABLED = 15874
EDENSE_CONCURRENT_LIMIT = 15875
EAGGR_MIGRATE_CORE = 15876
ESHUTDOWN_INPROGRESS = 15877
ENOT_HOMED_TO_PARTNER = 15878
ENOT_SFO_HA_POLICY = 15879
EAGGR_FAILED_LIMBO = 15880
EAGGR_MIGRATE_OFFLINE_FAILED = 15881
EAGGR_MIGRATING = 15882
EAGGR_MIGRATE_VETO = 15883
EDENSE_VOL_NOT_TRANSITIONED = 15884
ESNAPMIRRORVOLUMENOTQUIESCED = 15885
ESNAPMIRRORTRANSFERCOMPLETE = 15886
ESNAPMIRRORCHECKSUMERROR = 15887
ESNAPMIRRORNETWORKERROR = 15888
ESNAPMIRRORVOLUMEIDERROR = 15889
ESNAPMIRRORFILESYSTEMERROR = 15890
ESNAPMIRRORCHECKERDIFFSNAPSHOTS = 15891
EOP_DISALLOWED_ON_BUSY_MIRROR = 15892
EOP_DISALLOWED_ON_LOADSHARING_VOL = 15893
EOP_DISALLOWED_ON_CLONE_PARENT = 15894
EOP_DISALLOWED_ON_BACKUP_ACTIVE_VOL = 15895
EOP_DISALLOWED_ON_STRIPED_VOL = 15896
EOP_DISALLOWED_ON_COMPRESSED_VOL = 15897
EOP_DISALLOWED_ON_7MODE_VOL = 15898
EOP_DISALLOWED_ON_VOL_ALREADY_ON_AGGR = 15899
ESNAPMIRRORUNDELETEDSNAPSHOTONDEST = 15900
ESNAPMIRRORENGINETYPENOTSPECIFIED = 15901
ESNAPMIRRORMISMATCHEDSNAPSHOTLISTS = 15902
ESNAPMIRRORDESTINATIONNOTRESTRICTED = 15903
ESNAPMIRRORDESTINATIONNOTEMPTY = 15904
ESNAPMIRRORNOSNAPLOCKVOLUME = 15905
ESNAPMIRRORNOCOMPRESSEDVOLUME = 15906
ESNAPMIRRORDESTVOLTOOSMALL = 15907
EROOTVOL_NOT_FULLY_GUARANTEED = 15908
EVOL_FRACTIONAL_RESERVE_INVALID_FOR_ROOT = 15909
EVOL_FRACTIONAL_RESERVE_INVALID_FOR_PENDING_ROOT = 15910
EVOL_FRACTIONAL_RESERVE_INVALID_FOR_IRON_ROOT = 15911
EOP_64BIT_UPGRADE_SCANNER_DISABLED = 15912
E_ADDRFAMILY = 16000
E_AGAIN = 16001
E_BADFLAGS = 16002
E_FAMILY = 16004
E_MEMORY = 16005
E_NODATA = 16006
E_NONAME = 16007
E_SERVICE = 16008
E_SOCKTYPE = 16009
E_SYSTEM = 16010
E_BADHINTS = 16011
E_PROTOCOL = 16012
E_NXDOMAIN = 16013
E_RESNULL = 16014
E_MAX = 16015
EDISKASSIGNFAIL = 16016
ENOFMMDEVICES = 16017
EVFILERMONITORNOTSTARTED = 16018
EFCMON_GENERATION = 16019
EFCMON_INVALID_CONFIG = 16020
EVOLMOVEJOBNOTINCUTOVERDEFERRED = 16021
EVOLMOVEJOBSIGNALSENDFAILED = 16022
E_VOL_MOVE_NOT_COMPATIBLE_VERSION = 16023
E_VOL_MOVE_DC_NOT_ALLOWED = 16024
E_OP_DISALLOWED_ON_AGGR_NOT_IN_VSERVER_LIST = 16025
E_OP_UNSUPPORTED_NO_SPACE_ON_DESTINATION_AGGR = 16026
EINVALIDUSERNAME = 16030
EROLENOTFOUND = 16031
EINVALIDAPPLICATION = 16032
EROLECONFIGNOTFOUND = 16033
EUSERNOTFOUND = 16034
EINVALIDACCESS = 16035
EUSERLOCKFAILED = 16036
EUSERUNLOCKFAILED = 16037
ECMDDIRNOTFOUND = 16039
EINVALIDROLENAME = 16040
EINVALIDCMDDIRNAME = 16041
EINVALIDQUERY = 16042
EAPPLICATIONNOTFOUND = 16043
EAUTHENTICATIONMETHODNOTFOUND = 16044
ESTRIPEDVOL_PRIVILEGELEVEL = 16501
EVOLUME_DEST_STRIPED_VOL_NAME_NOT_ALLOWED = 16502
EVOLUME_FLEX_TO_STRIPED_NOT_ALLOWED = 16503
ECANTQUIESCELASTPATH = 16504
EINVALIDTARGET = 16505
ELUNQUIESCING = 16506
ERESUMEFAILED = 16507
EQUIESCEFAILED = 16508
EQUIESCENOTSUPPORTED = 16509
EONTAPI_VOLTRANS_GOINGHOME = 16510
EONTAPI_VOLTRANS_VOLNOTFOUND = 16511
E_DIRECTORY_CHANGED = 16512
EOP_DISALLOWED_ON_SPARSE_VOL = 16513
EOP_DISALLOWED_ON_AGGR_WITH_SPARSE_VOL = 16514
EPARTNERDISKONLY = 16515
EAGGR_MIGRATE_HA_MSG_ERR = 16516
EAGGR_MIGRATE_ONLINE_TIMEOUT = 16517
EAGGR_MIGRATE_ONLINE_FAILED = 16518
EVOLUMENOTLOCAL = 16600
EVOLUME_RELSTATUS_UNKNOWN = 16601
ESNAPMIRRORDBLADEABORT = 16602
ESNAPMIRRORSCANNINGBLOCKMETADATA = 16603
ESNAPMIRROR_REF_OR_XFER_SNAPSHOT_DELETED = 16604
ESNAPMIRRORUNKNOWNFSVERSION = 16605
ESNAPMIRRORJUMPAHEADFAILED = 16606
ECKSUMNOTKNOWN = 17000
ECKSUMTYPEMISMATCH = 17001
EINVENTORYMISMATCH = 17002
EPARENTNOTONLINE = 17003
ESOURCE_ISNOT_LOCAL_VOLUME = 17100
EDEST_ISNOT_LOCAL_VOLUME = 17101
ESOURCE_IS_LS_VOLUME = 17102
ESOURCE_ISNOT_LS_VOLUME = 17103
ESOURCE_DEST_SAME = 17104
ESOURCE_IS_DIFFERENT = 17105
ESOURCE_IS_EXISTING_DEST_VOLUME = 17106
ESOURCE_VOLUME_HAS_CACHE = 17107
ESOURCE_ISNOT_RW_VOLUME = 17108
ESOURCE_IS_STRIPED_VOLUME = 17110
EDEST_ISNOT_LS_VOLUME = 17111
EDEST_IS_EXISTING_SOURCE_VOLUME = 17112
EDEST_IS_EXISTING_DEST_VOLUME = 17113
EDEST_ISNOT_DP_VOLUME = 17114
EDEST_IS_RW_VOLUME = 17115
EDEST_VOLUME_IN_LS_RELATION = 17116
EDEST_VOLUME_NOT_EMPTY = 17117
EDEST_VOLUME_HAS_CACHE = 17118
EDEST_IS_CACHE_VOLUME = 17119
EDEST_VOLUME_NOT_INITIALIZED = 17120
EDEST_IS_STRIPED_VOLUME = 17121
ERELATION_EXISTS = 17122
ENOSNAPSHOT_COPY = 17123
EOP_FROM_NONMGR_VSERVER = 17124
EEMPTY_VOLUMES = 17125
ESCHEDULE_DOESNT_EXIST = 17126
ERELATION_NOT_QUIESCED = 17127
ERELATION_IS_QUIESCED = 17128
ESOURCE_DEST_VSERVERS_DIFFERENT = 17129
ENOTRANSFER_IN_PROGRESS = 17130
EANOTHER_OP_ACTIVE = 17131
EDEST_LS_VOLUME_CURRENT = 17132
EDEST_VOLUME_OFFLINE = 17133
ELS_SET_DEST_VOLUMES_NOT_CURRENT = 17134
ELS_SET_ISNOT_INITIALIZED = 17135
ETRIES_COUNT_IS_ZERO = 17136
ETRANSFER_IN_PROGRESS = 17137
EDEST_MIRROR_ENGINE_INCOMPATIBLE = 17138
ENOCHECK_IN_PROGRESS = 17139
EVOLUMES_WITH_DIFF_STRIPES = 17140
EFAILOVER = 17141
EDEST_IS_LS_VOLUME = 17142
ESIS_CLONE_VFILER_ACCESS = 17143
ESPARSE_TOO_MANY_SPARSE_VOLS = 17144
ESPARSE_VOL_CREATE_FAILED = 17145
ESPARSE_UNKNOWN_PROTOCOL = 17146
ESPARSE_SRC_VOL_UNAVAILABLE = 17147
ESPARSE_SRC_VOL_NOT_FLEX = 17148
ESPARSE_SRC_VOL_WORM = 17149
EVOL_CLONE_BEING_SPLIT = 17151
EVOL_MOVING_PARENT_VOL_RETRY = 17152
EAGGR_READONLY = 17153
EVOL_LOCKED_SNAPSHOTS = 17154
EVOL_SCAN_INIT_FAILED = 17155
EDISKFAILED = 17156
ESNAPMIRRORCLONERESYNCERROR = 17157
E_VOLUME_INACCESSIBLE = 17158
EVOLEXISTS = 17159
ESNAPMIRROR_JOB_INITIATED_ABORT = 17160
ESIS_CLONE_CLONE_SUB_COMPRESSION = 17161
EDEST_IS_VOLUME_CLONE = 17162
ESIS_CLONE_MAX_DENSE_LIMIT_REACHED = 17163
ESPARSE_SRC_VOL_INDEX_DIR = 17164
EDEST_VOL_LOCKED = 18020
ESRC_VOL_LOCKED = 18021
EVOLUME_FS_SIZE_FIXED = 18022
ESNAPMIRRORVMALIGNNOTSUPPORTED = 18023
EVOLUME_IRON_NON_LOCAL_STATUS = 18024
EVOLUME_UNSUPPORTED_OPTION_VMALIGN = 18025
EVOLUME_64BIT_UPGRADE_VVOL_ENOSPC_OVERWRITE = 18026

                                                                                                                                                                                                                                                                        NaServer.py                                                                                         0000644 0000000 0000000 00000072471 13452554242 011674  0                                                                                                    ustar   root                            root                                                                                                                                                                                                                   #============================================================#
#                                                            #
# $ID:$                                                      #
#                                                            #
# NaServer.py                                                #
#                                                            #
# Client-side interface to ONTAP and DataFabric Manager APIs.#
#                                                            #
# Copyright (c) 2011 NetApp, Inc. All rights reserved.       #
# Specifications subject to change without notice.           #
#                                                            #
#============================================================#

__version__ = "1.0"

from NaElement import *

import base64
import xml.parsers.expat
import socket

ssl_import = True
try:
    import ssl
except ImportError:
    ssl_import = False
    pass


python_version = float(str(sys.version_info[0]) + "." + str(sys.version_info[1]))

socket_ssl_attr = True
if(python_version < 3.0):
    import httplib
    if(hasattr(socket, 'ssl') != True):
        socket_ssl_attr = False
else :
    import http.client
    httplib = http.client
	
#dtd files
FILER_dtd = "file:/etc/netapp_filer.dtd"
DFM_dtd = "file:/etc/netapp_dfm.dtd"
AGENT_dtd = "file:/etc/netapp_agent.dtd"

#URLs
AGENT_URL = "/apis/XMLrequest"
FILER_URL = "/servlets/netapp.servlets.admin.XMLrequest_filer"
NETCACHE_URL = "/servlets/netapp.servlets.admin.XMLrequest"
DFM_URL = "/apis/XMLrequest"

ZAPI_xmlns = "http://www.netapp.com/filer/admin"

NMSDK_VERSION = "5.3.1"
NMSDK_LANGUAGE = "Python"
nmsdk_app_name = ""

class NaServer :
    """Class for managing Network Appliance(r) Storage System
    using ONTAPI(tm) and DataFabric Manager API(tm).

    An NaServer encapsulates an administrative connection to
    a NetApp Storage Systems running Data ONTAP 6.4 or later.
    NaServer can also be used to establish connection with
    OnCommand Unified Manager server (OCUM). You construct NaElement
    objects that represent queries or commands, and use invoke_elem()
    to send them to the storage systems or OCUM server. Also,
    a convenience routine called invoke() can be used to bypass
    the element construction step.  The return from the call is
    another NaElement which either has children containing the
    command results, or an error indication.

    The following routines are available for setting up
    administrative connections to a storage system or OCUM server.
    """



    def __init__(self, server, major_version, minor_version):
        """Create a new connection to server 'server'.  Before use,
    you either need to set the style to "hosts.equiv" or set
    the username (always "root" at present) and password with
    set_admin_user().
    """

        self.server = server
        self.major_version = major_version
        self.minor_version = minor_version
        self.transport_type = "HTTP"
        self.port = 80
        self.user = "root"
        self.password = ""
        self.style = "LOGIN"
        self.timeout = None
        self.vfiler = ""
        self.server_type = "FILER"
        self.debug_style = ""
        self.xml = ""
        self.originator_id = ""
        self.cert_file = None
        self.key_file = None
        self.ca_file = None
        self.need_cba = False;
        self.need_server_auth = False
        self.need_cn_verification = False
        self.url = FILER_URL
        self.dtd = FILER_dtd
        self.ZAPI_stack = []
        self.ZAPI_atts = {}



    def set_style(self, style):
        """Pass in 'LOGIN' to cause the server to use HTTP simple
    authentication with a username and password.  Pass in 'HOSTS'
    to use the hosts.equiv file on the filer to determine access
    rights (the username must be root in that case). Pass in
    'CERTIFICATE' to use certificate based authentication with the
    DataFabric Manager server.
    If style = CERTIFICATE, you can use certificates to authenticate
    clients who attempt to connect to a server without the need of
    username and password. This style will internally set the transport
    type to HTTPS. Verification of the server's certificate is required
    in order to properly authenticate the identity of the server.
    Server certificate verification will be enabled by default using this
    style and Server certificate verification will always enable hostname
    verification. You can disable server certificate (with hostname)
    verification using set_server_cert_verification().
    """

        if(style != "HOSTS" and style != "LOGIN" and style != "CERTIFICATE"):
            return self.fail_response(13001,"in NaServer::set_style: bad style \""+style+"\"")

        if (style == "CERTIFICATE") :
            if (ssl_import == False):
                return self.fail_response(13001,"in NaServer::set_style: \""+style+"\" cannot be used as 'ssl' module is not imported.")
            if (socket_ssl_attr == False):
                return self.fail_response(13001,"in NaServer::set_style: \""+style+"\" cannot be used as 'socket' module is not compiled with SSL support.")
            ret = self.set_transport_type("HTTPS")
            if (ret):
                return ret
            self.need_cba = True
            self.set_server_cert_verification(True)
        else :
            self.need_cba = False
            self.set_server_cert_verification(False)
        self.style = style
        return None



    def get_style(self):
        """Get the authentication style
    """

        return self.style



    def set_admin_user(self, user, password):
        """Set the admin username and password.  At present 'user' must
    always be 'root'.
    """

        self.user = user
        self.password = password



    def set_server_type(self, server_type):
        """Pass in one of these keywords: 'FILER' or 'DFM' or 'OCUM' to indicate
    whether the server is a storage system (filer) or a OCUM server.

    If you also use set_port(), call set_port() AFTER calling this routine.

    The default is 'FILER'.
    """

        if (server_type.lower() == 'filer'):
            self.url = FILER_URL
            self.dtd = FILER_dtd

        elif (server_type.lower() ==  'netcache'):
            self.url = NETCACHE_URL
            self.port = 80

        elif (server_type.lower() ==  'agent'):
            self.url = AGENT_URL
            self.port = 4092
            self.dtd = AGENT_dtd

        elif (server_type.lower() ==  'dfm'):
            self.url = DFM_URL
            self.port = 8088
            self.dtd = DFM_dtd

            if(self.transport_type == "HTTPS") :
                self.port = 8488

        elif (server_type.lower() ==  'ocum'):
            self.url = DFM_URL
            self.port = 443
            self.transport_type = "HTTPS"
            self.dtd = DFM_dtd


        else :
            return self.fail_response(13001,"in NaServer::set_server_type: bad type \""+server_type+"\"")

        self.server_type = server_type
        return None



    def get_server_type(self):
        """Get the type of server this server connection applies to.
    """

        return self.server_type



    def set_vserver(self, vserver):
        """Sets the vserver name. This function is added for vserver-tunneling.
    However, vserver tunneling actually uses vfiler-tunneling. Hence this
    function internally sets the vfiler name.
        """

        if(self.major_version >= 1 and self.minor_version >= 15):
            self.vfiler = vserver
            return 1

        print("\nONTAPI version must be at least 1.15 to send API to a vserver\n")
        return 0


    def get_vserver(self):
        """Gets the vserver name. This function is added for vserver-tunneling.
    However, vserver tunneling actually uses vfiler-tunneling. Hence this
    function actually returns the vfiler name.
        """

        return self.vfiler



    def set_originator_id(self, originator_id):
        """Function to set the originator_id before executing any ONTAP API.
        """

        self.originator_id = originator_id
        return 1


    def get_originator_id(self):
        """Gets the originator_id for the given server context on which the
    ONTAP API commands get invoked.
        """

        return self.originator_id



    def set_transport_type(self, scheme):
        """Override the default transport type.  The valid transport
    type are currently 'HTTP' and 'HTTPS'.
    """

        if(scheme != "HTTP" and scheme != "HTTPS"):
            return self.fail_response(13001,"in NaServer::set_transport_type: bad type \" "+scheme+"\"")

        if(scheme == "HTTP"):
            if(self.server_type == "OCUM"):
                return self.fail_response(13001,"Server type '" + self.server_type + "' does not support '" + scheme + "' transport type")

            self.transport_type = "HTTP"

            if(self.server_type == "DFM"):
                self.port = 8088

            else :
                self.port = 80


        if(scheme == "HTTPS"):
            if (socket_ssl_attr == False):
                return self.fail_response(13001,"in NaServer::set_transport_type: \""+scheme+"\" transport cannot be used as 'socket' module is not compiled with SSL support.")

            self.transport_type = "HTTPS"

            if(self.server_type == "DFM"):
                self.port = 8488

            else :
                self.port = 443

        return None



    def get_transport_type(self):
        """Retrieve the transport used for this connection.
    """

        return self.transport_type



    def set_debug_style(self, debug_style):
        """Set the style of debug.
    """

        if(debug_style != "NA_PRINT_DONT_PARSE"):
            return self.fail_response(13001,"in NaServer::set_debug_style: bad style \""+debug_style+"\"")

        else :
            self.debug_style = debug_style
            return



    def set_port(self, port):
        """Override the default port for this server.  If you
    also call set_server_type(), you must call it before
    calling set_port().
    """

        self.port = port



    def get_port(self):
        """Retrieve the port used for the remote server.
    """

        return self.port



    def is_debugging(self):
        """Check the type of debug style and return the
    value for different needs. Return 1 if debug style
    is NA_PRINT_DONT_PARSE,    else return 0.
    """

        if(self.debug_style == "NA_PRINT_DONT_PARSE"):
            return 1

        else :
            return 0



    def get_raw_xml_output(self):
        """Return the raw XML output.
    """

        return self.xml



    def set_raw_xml_output(self, xml):
        """Save the raw XML output.
    """

        self.xml = xml



    def use_https(self):
        """Determines whether https is enabled.
    """

        if(self.transport_type == "HTTPS"):
            return 1

        else :
            return 0



    def invoke_elem(self, req):
        """Submit an XML request already encapsulated as
        an NaElement and return the result in another
        NaElement.
        """
     
        server = self.server
        user = self.user
        password = self.password
        debug_style = self.debug_style
        vfiler = self.vfiler
        originator_id = self.originator_id
        server_type = self.server_type
        xmlrequest = req.toEncodedString()
        url = self.url
        vfiler_req = ""
        originator_id_req = ""
        nmsdk_app_req = ""

        try:

            if(self.transport_type == "HTTP"):
                    if(python_version < 2.6):  # python versions prior to 2.6 do not support 'timeout'
                        connection = httplib.HTTPConnection(server, port=self.port)
                    else :
                        connection = httplib.HTTPConnection(server, port=self.port, timeout=self.timeout)

            else : # for HTTPS

                    if (self.need_cba == True or self.need_server_auth == True):
                        if (python_version < 2.6):
                            cba_err = "certificate based authentication is not supported with Python " + str(python_version) + "." 
                            return self.fail_response(13001, cba_err) 
                        connection = CustomHTTPSConnection(server, self.port, key_file=self.key_file, 
                        cert_file=self.cert_file, ca_file=self.ca_file, 
                        need_server_auth=self.need_server_auth, 
                        need_cn_verification=self.need_cn_verification, 
                        timeout=self.timeout)
                        connection.connect()
                        if (self.need_cn_verification == True):
                            cn_name = connection.get_commonName()
                            if (cn_name.lower() != server.lower()) :
                                cert_err = "server certificate verification failed: server certificate name (CN=" + cn_name + "), hostname (" + server + ") mismatch."
                                connection.close()
                                return self.fail_response(13001, cert_err)
                    else :
                        if(python_version < 2.6): # python versions prior to 2.6 do not support 'timeout'
                            connection = httplib.HTTPSConnection(server, port=self.port)
                        else :
                            connection = httplib.HTTPSConnection(server, port=self.port, timeout=self.timeout)

            connection.putrequest("POST", self.url)
            connection.putheader("Content-type", "text/xml; charset=\"UTF-8\"")

            if(self.get_style() != "HOSTS"):

                if(python_version < 3.0):
                    base64string = base64.encodestring("%s:%s" %(user,password))[:-1]
                    authheader = "Basic %s" %base64string
                elif(python_version == 3.0):
                    base64string = base64.encodestring(('%s:%s' %( user, password)).encode())
                    authheader = "Basic %s" % base64string.decode().strip()
                else:
                    base64string = base64.encodebytes(('%s:%s' %( user, password)).encode())
                    authheader = "Basic %s" % base64string.decode().strip()

                connection.putheader("Authorization", authheader)

            if(vfiler != ""):
                vfiler_req = " vfiler=\"" + vfiler + "\""

            if(originator_id != ""):
                originator_id_req = " originator_id=\"" + originator_id + "\""

            if(nmsdk_app_name != ""):
                nmsdk_app_req = " nmsdk_app=\"" + nmsdk_app_name + "\"";

            content = '<?xml version=\'1.0\' encoding=\'utf-8\'?>'\
                     +'\n'+\
                     '<!DOCTYPE netapp SYSTEM \'' + self.dtd + '\''\
                     '>' \
                     '<netapp' \
                     + vfiler_req + originator_id_req + \
                     ' version="'+str(self.major_version)+'.'+str(self.minor_version)+'"'+' xmlns="' + ZAPI_xmlns  + "\"" \
                     + " nmsdk_version=\"" + NMSDK_VERSION + "\"" \
                     + " nmsdk_platform=\"" + NMSDK_PLATFORM + "\"" \
                     + " nmsdk_language=\"" + NMSDK_LANGUAGE + "\"" \
                     + nmsdk_app_req \
                     + ">" \
                     + xmlrequest + '</netapp>'

            if(debug_style == "NA_PRINT_DONT_PARSE"):
                print(("INPUT \n" +content))

            if(python_version < 3.0):
                connection.putheader("Content-length", len(content))
                connection.endheaders()
                connection.send(content)
            else :
                connection.putheader("Content-length", str(len(content)))
                connection.endheaders()
                connection.send(content.encode())


        except socket.error :
            message = sys.exc_info()
            return (self.fail_response(13001, message[1]))

        response = connection.getresponse()
    
        if not response :
            connection.close()
            return self.fail_response(13001,"No response received")

        if(response.status == 401):
            connection.close()
            return self.fail_response(13002,"Authorization failed")

        xml_response = response.read()

        if(self.is_debugging() > 0):

            if(debug_style != "NA_PRINT_DONT_PARSE"):
                self.set_raw_xml_output(xml_response)
                print(("\nOUTPUT :",xml_response,"\n"))
                connection.close()
                return self.fail_response(13001, "debugging bypassed xml parsing")
        
        connection.close()
        return self.parse_xml(xml_response)



    def invoke(self, api, *arg):
        """A convenience routine which wraps invoke_elem().
    It constructs an NaElement with name $api, and for
    each argument name/value pair, adds a child element
    to it.  It's an error to have an even number of
    arguments to this function.

    Example: myserver->invoke('snapshot-create',
                                    'snapshot', 'mysnapshot',
                                'volume', 'vol0');
    """

        num_parms = len(arg)

        if ((num_parms & 1)!= 0):
            return self.fail_response(13001,"in Zapi::invoke, invalid number of parameters")

        xi = NaElement(api)
        i = 0

        while(i < num_parms):
            key = arg[i]
            i = i+1
            value = arg[i]
            i = i+1
            xi.child_add(NaElement(key, value))

        return self.invoke_elem(xi)



    def set_vfiler(self, vfiler_name):
        """Sets the vfiler name. This function is used
    for vfiler-tunneling.
    """

        if(self.major_version >= 1 and self.minor_version >= 7 ):
                self.vfiler = vfiler_name
                return 1

        return 0


    def set_timeout(self, timeout):
        """Sets the connection timeout value, in seconds,
    for the given server context.
    """

        if (python_version < 2.6):
            print("\nPython versions prior to 2.6 do not support timeout.\n")
            return
        self.timeout = timeout



    def get_timeout(self):
        """Retrieves the connection timeout value (in seconds)
    for the given server context.
    """

        return self.timeout

    def set_client_cert_and_key(self, cert_file, key_file):
        """ Sets the client certificate and key files that are required for client authentication
        by the server using certificates. If key file is not defined, then the certificate file 
        will be used as the key file.
        """

        self.cert_file = cert_file
        if (key_file != None):
            self.key_file = key_file
        else:
            self.key_file = cert_file

    def set_ca_certs(self, ca_file):
        """ Specifies the certificates of the Certificate Authorities (CAs) that are 
        trusted by this application and that will be used to verify the server certificate.
        """

        self.ca_file = ca_file

    def set_server_cert_verification(self, enable):
        """ Enables or disables server certificate verification by the client.
        Server certificate verification is enabled by default when style 
        is set to CERTIFICATE. Hostname (CN) verification is enabled 
        during server certificate verification. Hostname verification can be 
        disabled using set_hostname_verification() API.
        """

        if (enable != True and enable != False):
            return self.fail_response(13001, "NaServer::set_server_cert_verification: invalid argument " + str(enable) + " specified");
        if (not self.use_https()):
            return self.fail_response(13001,"in NaServer::set_server_cert_verification: server certificate verification can only be enabled or disabled for HTTPS transport")
        if (enable == True and ssl_import == False):
            return self.fail_response(13001,"in NaServer::set_server_cert_verification: server certificate verification cannot be used as 'ssl' module is not imported.")
        self.need_server_auth = enable
        self.need_cn_verification = enable
        return None

    def is_server_cert_verification_enabled(self):
        """ Determines whether server certificate verification is enabled or not.
        Returns True if it is enabled, else returns False
        """

        return self.need_server_auth

    def set_hostname_verification(self, enable):
        """  Enables or disables hostname verification during server certificate verification.
        Hostname (CN) verification is enabled by default during server certificate verification. 
        """

        if (enable != True and enable != False):
            return self.fail_response(13001, "NaServer::set_hostname_verification: invalid argument " + str(enable) + " specified")
        if (self.need_server_auth == False):
            return self.fail_response(13001, "in NaServer::set_hostname_verification: server certificate verification is not enabled")
        self.need_cn_verification = enable
        return None;

    def is_hostname_verification_enabled(self):
        """ Determines whether hostname verification is enabled or not.
        Returns True if it is enabled, else returns False
        """

        return self.need_cn_verification;

    ## "private" subroutines for use by the public routines


    ## This is used when the transmission path fails, and we don't actually
    ## get back any XML from the server.
    def fail_response(self, errno, reason):
        """This is a private function, not to be called from outside NaElement
        """
        n = NaElement("results")
        n.attr_set("status","failed")
        n.attr_set("reason",reason)
        n.attr_set("errno",errno)
        return n



    def start_element(self, name, attrs):
        """This is a private function, not to be called from outside NaElement
        """

        n = NaElement(name)
        self.ZAPI_stack.append(n)
        self.ZAPI_atts = {}
        attr_name = list(attrs.keys())
        attr_value = list(attrs.values())
        i = 0
        for att in attr_name :
            val = attr_value[i]
            i = i+1
            self.ZAPI_atts[att] = val
            n.attr_set(att,val)



    def end_element(self, name):
        """This is a private function, not to be called from outside NaElement
        """

        stack_len = len(self.ZAPI_stack)

        if (stack_len > 1):
            n = self.ZAPI_stack.pop(stack_len - 1)
            i = len(self.ZAPI_stack)

            if(i != stack_len - 1):
                print("pop did not work!!!!\n")

            self.ZAPI_stack[i-1].child_add(n)



    def char_data(self, data):
        """This is a private function, not to be called from outside NaElement
        """

        i = len(self.ZAPI_stack)
        data = NaElement.escapeHTML(data)
        self.ZAPI_stack[i-1].add_content(data)



    def parse_xml(self, xmlresponse):
        """This is a private function, not to be called from outside NaElement
        """
        p = xml.parsers.expat.ParserCreate()
        p.StartElementHandler = self.start_element
        p.EndElementHandler = self.end_element
        p.CharacterDataHandler = self.char_data
        p.Parse(xmlresponse, 1)
        stack_len = len(self.ZAPI_stack)

        if(stack_len <= 0):
            return self.fail_response(13001,"Zapi::parse_xml-no elements on stack")

        r = self.ZAPI_stack.pop(stack_len - 1)

        if (r.element['name'] != "netapp") :
            return self.fail_response(13001, "Zapi::parse_xml - Expected <netapp> element but got " + r.element['name'])

        results = r.child_get("results")

        if (results == None) :
            return self.fail_response(13001, "Zapi::parse_xml - No results element in output!")

        return results



    def parse_raw_xml(self, xmlrequest):
        """This is a private function, not to be called from outside NaElement
        """

        p = xml.parsers.expat.ParserCreate()
        p.StartElementHandler = self.start_element
        p.EndElementHandler = self.end_element
        p.CharacterDataHandler = self.char_data
        p.Parse(xmlrequest,1)
        stack_len = len(self.ZAPI_stack)

        if(stack_len <= 0):
            return self.fail_response(13001,"Zapi::parse_xml-no elements on stack")

        r = self.ZAPI_stack.pop(stack_len - 1)

        return r


    @staticmethod
    def set_application_name (app_name):
        """ Sets the name of the client application.
        """

        global nmsdk_app_name
        nmsdk_app_name = app_name

    @staticmethod
    def get_application_name ():
        """ Returns the name of the client application.
        """

        global nmsdk_app_name
        return nmsdk_app_name


    @staticmethod
    def get_platform_info():
        """ Returns the platform information.
        """

        systemType = "Unknown"
        osName = ""
        processor = ""
        osInfo = ""

        try:
            import platform
            systemType = platform.system()
            if (systemType == "Windows" or systemType == "Microsoft"):
                systemType = "Windows"
                if(python_version < 3.0):
                    import _winreg
                    handle = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion")
                    (osName, type) = _winreg.QueryValueEx(handle, "ProductName")
                    _winreg.CloseKey(handle)
                    handle = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, "SYSTEM\\ControlSet001\\Control\\Session Manager\\Environment")
                    (processor, type) = _winreg.QueryValueEx(handle, "PROCESSOR_ARCHITECTURE")
                    _winreg.CloseKey(handle)
                else:
                    import winreg
                    handle = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion")
                    (osName, type) = winreg.QueryValueEx(handle, "ProductName")
                    winreg.CloseKey(handle)
                    handle = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, "SYSTEM\\ControlSet001\\Control\\Session Manager\\Environment")
                    (processor, type) = winreg.QueryValueEx(handle, "PROCESSOR_ARCHITECTURE")
                    winreg.CloseKey(handle)
                osInfo = osName + " " + processor
            else:
                import os
                if (systemType == "Linux"):
                    import re
                    pipe = ""
                    if os.path.isfile("/etc/SuSE-release"):
                        pipe = os.popen('head -n 1 /etc/SuSE-release')
                    else:
                        pipe = os.popen("head -n 1 /etc/issue")
                    osName = pipe.readline()
                    pipe.close()
                    osName = osName.rstrip()
                    m = re.search("(.*?) \(.*?\)", osName)
                    if m:
                        osName = m.groups()[0]
                    pipe = os.popen('uname -p')
                    processor = pipe.readline()
                    pipe.close()
                    processor = processor.rstrip()
                    osInfo = osName + " " + processor
                elif (systemType == 'SunOS'):
                    pipe = os.popen('uname -srp')
                    unameInfo = pipe.readline()
                    pipe.close()
                    unameInfo = unameInfo.rstrip()
                    pipe = os.popen('isainfo -b')
                    isaInfo = pipe.readline()
                    pipe.close()
                    isaInfo = isaInfo.rstrip()
                    isaInfo += "-bit"
                    osInfo = unameInfo + " " + isaInfo
                elif (systemType == 'HP-UX'):
                    pipe = os.popen('uname -srm')
                    osInfo = pipe.readline()
                    pipe.close()
                    osInfo = osInfo.rstrip()
                elif (systemType == 'FreeBSD'):
                    pipe = os.popen('uname -srm')
                    osInfo = pipe.readline()
                    pipe.close()
                    osInfo = osInfo.rstrip()
                else:
                    osInfo = systemType
        except:
            osInfo = systemType
        return osInfo

NMSDK_PLATFORM = NaServer.get_platform_info()

try:
    class CustomHTTPSConnection(httplib.HTTPSConnection):
        """ Custom class to make a HTTPS connection, with support for Certificate Based Authentication"""

        def __init__(self, host, port, key_file, cert_file, ca_file, 
                   need_server_auth, need_cn_verification, timeout=None):
            httplib.HTTPSConnection.__init__(self, host, port=port, key_file=key_file, 
                                     cert_file=cert_file,timeout=timeout)
            self.key_file = key_file
            self.cert_file = cert_file
            self.ca_file = ca_file
            self.timeout = timeout
            self.need_server_auth = need_server_auth
            self.need_cn_verification = need_cn_verification

        def connect(self):
            sock = socket.create_connection((self.host, self.port), self.timeout)

            if (self.need_server_auth == True):
                self.sock = ssl.wrap_socket(sock, self.key_file, self.cert_file, ca_certs=self.ca_file, cert_reqs=ssl.CERT_REQUIRED)
            else:
                self.sock = ssl.wrap_socket(sock, self.key_file, self.cert_file, ca_certs=self.ca_file)

        def get_commonName(self):
            cert = self.sock.getpeercert()
            for x in cert['subject'] :
                if (x[0][0].lower() == 'commonname') :
                    return x[0][1]
            return ""
except AttributeError:
    pass




                                                                                                                                                                                                       NaServer.pyc                                                                                        0000644 0000000 0000000 00000062414 13452554441 012034  0                                                                                                    ustar   root                            root                                                                                                                                                                                                                   �
�ت\c           @   s|  d  Z  d d l Td d l Z d d l Z d d l Z e Z y d d l Z Wn e	 k
 rc e
 Z n Xe e e j d � d e e j d � � Z e Z e d k  r� d d l Z e e d � e k r� e
 Z n  n d d l Z e j Z d	 Z d
 Z d Z d Z d Z d Z d Z d Z d Z d Z d a  d f  d �  �  YZ! e! j" �  Z# y d e j$ f d �  �  YZ% Wn e& k
 rwn Xd S(   s   1.0i����(   t   *Ni    t   .i   g      @t   ssls   file:/etc/netapp_filer.dtds   file:/etc/netapp_dfm.dtds   file:/etc/netapp_agent.dtds   /apis/XMLrequests0   /servlets/netapp.servlets.admin.XMLrequest_filers*   /servlets/netapp.servlets.admin.XMLrequests!   http://www.netapp.com/filer/admins   5.3.1t   Pythont    t   NaServerc           B   s  e  Z d  Z d �  Z d �  Z d �  Z d �  Z d �  Z d �  Z d �  Z	 d �  Z
 d	 �  Z d
 �  Z d �  Z d �  Z d �  Z d �  Z d �  Z d �  Z d �  Z d �  Z d �  Z d �  Z d �  Z d �  Z d �  Z d �  Z d �  Z d �  Z d �  Z d �  Z d �  Z d �  Z  d �  Z! d  �  Z" d! �  Z# d" �  Z$ d# �  Z% d$ �  Z& e' d% �  � Z( e' d& �  � Z) e' d' �  � Z* RS((   sX  Class for managing Network Appliance(r) Storage System
    using ONTAPI(tm) and DataFabric Manager API(tm).

    An NaServer encapsulates an administrative connection to
    a NetApp Storage Systems running Data ONTAP 6.4 or later.
    NaServer can also be used to establish connection with
    OnCommand Unified Manager server (OCUM). You construct NaElement
    objects that represent queries or commands, and use invoke_elem()
    to send them to the storage systems or OCUM server. Also,
    a convenience routine called invoke() can be used to bypass
    the element construction step.  The return from the call is
    another NaElement which either has children containing the
    command results, or an error indication.

    The following routines are available for setting up
    administrative connections to a storage system or OCUM server.
    c         C   s�   | |  _  | |  _ | |  _ d |  _ d |  _ d |  _ d |  _ d |  _ d |  _	 d |  _
 d |  _ d |  _ d |  _ d |  _ d |  _ d |  _ d |  _ t |  _ t |  _ t |  _ t |  _ t |  _ g  |  _ i  |  _ d S(   s�   Create a new connection to server 'server'.  Before use,
    you either need to set the style to "hosts.equiv" or set
    the username (always "root" at present) and password with
    set_admin_user().
    t   HTTPiP   t   rootR   t   LOGINt   FILERN(   t   servert   major_versiont   minor_versiont   transport_typet   portt   usert   passwordt   stylet   Nonet   timeoutt   vfilert   server_typet   debug_stylet   xmlt   originator_idt	   cert_filet   key_filet   ca_filet   Falset   need_cbat   need_server_autht   need_cn_verificationt	   FILER_URLt   urlt	   FILER_dtdt   dtdt
   ZAPI_stackt	   ZAPI_atts(   t   selfR
   R   R   (    (    s   /root/src/manila/NaServer.pyt   __init__O   s0    																							c         C   s�   | d k r< | d k r< | d k r< |  j  d d | d � S| d k r� t t k rl |  j  d d | d � St t k r� |  j  d d | d	 � S|  j d
 � } | r� | St |  _ |  j t � n t |  _ |  j t � | |  _ d S(   s�  Pass in 'LOGIN' to cause the server to use HTTP simple
    authentication with a username and password.  Pass in 'HOSTS'
    to use the hosts.equiv file on the filer to determine access
    rights (the username must be root in that case). Pass in
    'CERTIFICATE' to use certificate based authentication with the
    DataFabric Manager server.
    If style = CERTIFICATE, you can use certificates to authenticate
    clients who attempt to connect to a server without the need of
    username and password. This style will internally set the transport
    type to HTTPS. Verification of the server's certificate is required
    in order to properly authenticate the identity of the server.
    Server certificate verification will be enabled by default using this
    style and Server certificate verification will always enable hostname
    verification. You can disable server certificate (with hostname)
    verification using set_server_cert_verification().
    t   HOSTSR   t   CERTIFICATEi�2  s#   in NaServer::set_style: bad style "s   "s   in NaServer::set_style: "s1   " cannot be used as 'ssl' module is not imported.sE   " cannot be used as 'socket' module is not compiled with SSL support.t   HTTPSN(
   t   fail_responset
   ssl_importR   t   socket_ssl_attrt   set_transport_typet   TrueR   t   set_server_cert_verificationR   R   (   R&   R   t   ret(    (    s   /root/src/manila/NaServer.pyt	   set_styleq   s     $			c         C   s   |  j  S(   s!   Get the authentication style
    (   R   (   R&   (    (    s   /root/src/manila/NaServer.pyt	   get_style�   s    c         C   s   | |  _  | |  _ d S(   sW   Set the admin username and password.  At present 'user' must
    always be 'root'.
    N(   R   R   (   R&   R   R   (    (    s   /root/src/manila/NaServer.pyt   set_admin_user�   s    	c         C   s'  | j  �  d k r' t |  _ t |  _ n� | j  �  d k rN t |  _ d |  _ n� | j  �  d k r~ t |  _ d |  _ t |  _ n� | j  �  d k r� t	 |  _ d |  _ t
 |  _ |  j d k rd	 |  _ qnQ | j  �  d
 k rt	 |  _ d |  _ d |  _ t
 |  _ n |  j d d | d � S| |  _ d S(   s�   Pass in one of these keywords: 'FILER' or 'DFM' or 'OCUM' to indicate
    whether the server is a storage system (filer) or a OCUM server.

    If you also use set_port(), call set_port() AFTER calling this routine.

    The default is 'FILER'.
    t   filert   netcacheiP   t   agenti�  t   dfmi�  R*   i(!  t   ocumi�  i�2  s(   in NaServer::set_server_type: bad type "s   "N(   t   lowerR    R!   R"   R#   t   NETCACHE_URLR   t	   AGENT_URLt	   AGENT_dtdt   DFM_URLt   DFM_dtdR   R+   R   R   (   R&   R   (    (    s   /root/src/manila/NaServer.pyt   set_server_type�   s0    												c         C   s   |  j  S(   s>   Get the type of server this server connection applies to.
    (   R   (   R&   (    (    s   /root/src/manila/NaServer.pyt   get_server_type�   s    c         C   s4   |  j  d k r+ |  j d k r+ | |  _ d Sd GHd S(   s�   Sets the vserver name. This function is added for vserver-tunneling.
    However, vserver tunneling actually uses vfiler-tunneling. Hence this
    function internally sets the vfiler name.
        i   i   s?   
ONTAPI version must be at least 1.15 to send API to a vserver
i    (   R   R   R   (   R&   t   vserver(    (    s   /root/src/manila/NaServer.pyt   set_vserver�   s
    	c         C   s   |  j  S(   s�   Gets the vserver name. This function is added for vserver-tunneling.
    However, vserver tunneling actually uses vfiler-tunneling. Hence this
    function actually returns the vfiler name.
        (   R   (   R&   (    (    s   /root/src/manila/NaServer.pyt   get_vserver�   s    c         C   s   | |  _  d S(   sJ   Function to set the originator_id before executing any ONTAP API.
        i   (   R   (   R&   R   (    (    s   /root/src/manila/NaServer.pyt   set_originator_id�   s    	c         C   s   |  j  S(   sm   Gets the originator_id for the given server context on which the
    ONTAP API commands get invoked.
        (   R   (   R&   (    (    s   /root/src/manila/NaServer.pyt   get_originator_id�   s    c         C   s  | d k r0 | d k r0 |  j  d d | d � S| d k r� |  j d k rn |  j  d d |  j d | d	 � Sd |  _ |  j d
 k r� d |  _ q� d |  _ n  | d k r� t t k r� |  j  d d | d � Sd |  _ |  j d
 k r� d |  _ q� d |  _ n  d S(   si   Override the default transport type.  The valid transport
    type are currently 'HTTP' and 'HTTPS'.
    R   R*   i�2  s,   in NaServer::set_transport_type: bad type " s   "t   OCUMs   Server type 's   ' does not support 's   ' transport typet   DFMi�  iP   s"   in NaServer::set_transport_type: "sO   " transport cannot be used as 'socket' module is not compiled with SSL support.i(!  i�  N(   R+   R   R   R   R-   R   R   (   R&   t   scheme(    (    s   /root/src/manila/NaServer.pyR.     s"    #		c         C   s   |  j  S(   s5   Retrieve the transport used for this connection.
    (   R   (   R&   (    (    s   /root/src/manila/NaServer.pyt   get_transport_type-  s    c         C   s5   | d k r$ |  j  d d | d � S| |  _ d Sd S(   s   Set the style of debug.
    t   NA_PRINT_DONT_PARSEi�2  s)   in NaServer::set_debug_style: bad style "s   "N(   R+   R   (   R&   R   (    (    s   /root/src/manila/NaServer.pyt   set_debug_style5  s    	c         C   s   | |  _  d S(   s�   Override the default port for this server.  If you
    also call set_server_type(), you must call it before
    calling set_port().
    N(   R   (   R&   R   (    (    s   /root/src/manila/NaServer.pyt   set_portB  s    c         C   s   |  j  S(   s2   Retrieve the port used for the remote server.
    (   R   (   R&   (    (    s   /root/src/manila/NaServer.pyt   get_portL  s    c         C   s   |  j  d k r d Sd Sd S(   s�   Check the type of debug style and return the
    value for different needs. Return 1 if debug style
    is NA_PRINT_DONT_PARSE,    else return 0.
    RK   i   i    N(   R   (   R&   (    (    s   /root/src/manila/NaServer.pyt   is_debuggingT  s    c         C   s   |  j  S(   s   Return the raw XML output.
    (   R   (   R&   (    (    s   /root/src/manila/NaServer.pyt   get_raw_xml_outputb  s    c         C   s   | |  _  d S(   s   Save the raw XML output.
    N(   R   (   R&   R   (    (    s   /root/src/manila/NaServer.pyt   set_raw_xml_outputj  s    c         C   s   |  j  d k r d Sd Sd S(   s)   Determines whether https is enabled.
    R*   i   i    N(   R   (   R&   (    (    s   /root/src/manila/NaServer.pyt	   use_httpsr  s    c         C   sy  |  j  } |  j } |  j } |  j } |  j } |  j } |  j } | j �  }	 |  j }
 d } d } d } y|  j	 d k r� t
 d k  r� t j | d |  j �} qt j | d |  j d |  j �} nQ|  j t k s� |  j t k r�t
 d k  rd t t
 � d } |  j d | � St | |  j d	 |  j d
 |  j d |  j d |  j d |  j d |  j �} | j �  |  j t k r| j �  } | j �  | j �  k r�d | d | d } | j �  |  j d | � SqnH t
 d k  r�t j | d |  j �} n! t j | d |  j d |  j �} | j d |  j � | j d d � |  j  �  d k rt
 d k  rt! j" d | | f � d  } d | } ny t
 d k r�t! j" d | | f j# �  � } d | j$ �  j% �  } n5 t! j& d | | f j# �  � } d | j$ �  j% �  } | j d | � n  | d k r(d | d } n  | d k rEd | d } n  t' d k rbd t' d } n  d d d  |  j( d! | | d" t |  j) � d t |  j* � d d# t+ d d$ t, d d% t- d d& t. d | d' |	 d( } | d) k rd* | GHn  t
 d k  r=| j d+ t/ | � � | j0 �  | j1 | � n9 | j d+ t t/ | � � � | j0 �  | j1 | j# �  � Wn1 t2 j3 k
 r�t4 j5 �  } |  j d | d, � SX| j6 �  } | s�| j �  |  j d d- � S| j7 d. k r | j �  |  j d/ d0 � S| j8 �  } |  j9 �  d1 k rb| d) k rb|  j: | � d2 | d f GH| j �  |  j d d3 � Sn  | j �  |  j; | � S(4   s   Submit an XML request already encapsulated as
        an NaElement and return the result in another
        NaElement.
        R   R   g������@R   R   s>   certificate based authentication is not supported with Python R   i�2  R   R   R   R   R   sD   server certificate verification failed: server certificate name (CN=s   ), hostname (s   ) mismatch.t   POSTs   Content-types   text/xml; charset="UTF-8"R(   g      @s   %s:%si����s   Basic %st   Authorizations	    vfiler="s   "s    originator_id="s    nmsdk_app="s&   <?xml version='1.0' encoding='utf-8'?>s   
s   <!DOCTYPE netapp SYSTEM 's	   '><netapps
    version="s    xmlns="s    nmsdk_version="s    nmsdk_platform="s    nmsdk_language="t   >s	   </netapp>RK   s   INPUT 
s   Content-lengthi   s   No response receivedi�  i�2  s   Authorization failedi    s	   
OUTPUT :s   debugging bypassed xml parsing(<   R
   R   R   R   R   R   R   t   toEncodedStringR!   R   t   python_versiont   httplibt   HTTPConnectionR   R   R   R/   R   t   strR+   t   CustomHTTPSConnectionR   R   R   R   t   connectt   get_commonNameR:   t   closet   HTTPSConnectiont
   putrequestt	   putheaderR3   t   base64t   encodestringt   encodet   decodet   stript   encodebytest   nmsdk_app_nameR#   R   R   t
   ZAPI_xmlnst   NMSDK_VERSIONt   NMSDK_PLATFORMt   NMSDK_LANGUAGEt   lent
   endheaderst   sendt   sockett   errort   syst   exc_infot   getresponset   statust   readRO   RQ   t	   parse_xml(   R&   t   reqR
   R   R   R   R   R   R   t
   xmlrequestR!   t
   vfiler_reqt   originator_id_reqt   nmsdk_app_reqt
   connectiont   cba_errt   cn_namet   cert_errt   base64stringt
   authheadert   contentt   messaget   responset   xml_response(    (    s   /root/src/manila/NaServer.pyt   invoke_elem~  s�    								$		

!�





c         G   s�   t  | � } | d @d k r, |  j d d � St | � } d } xN | | k  r� | | } | d } | | } | d } | j t | | � � qA W|  j | � S(   s�  A convenience routine which wraps invoke_elem().
    It constructs an NaElement with name $api, and for
    each argument name/value pair, adds a child element
    to it.  It's an error to have an even number of
    arguments to this function.

    Example: myserver->invoke('snapshot-create',
                                    'snapshot', 'mysnapshot',
                                'volume', 'vol0');
    i   i    i�2  s-   in Zapi::invoke, invalid number of parameters(   Rm   R+   t	   NaElementt	   child_addR�   (   R&   t   apit   argt	   num_parmst   xit   it   keyt   value(    (    s   /root/src/manila/NaServer.pyt   invoke  s    



c         C   s/   |  j  d k r+ |  j d k r+ | |  _ d Sd S(   sJ   Sets the vfiler name. This function is used
    for vfiler-tunneling.
    i   i   i    (   R   R   R   (   R&   t   vfiler_name(    (    s   /root/src/manila/NaServer.pyt
   set_vfiler"  s    	c         C   s"   t  d k  r d GHd S| |  _ d S(   sU   Sets the connection timeout value, in seconds,
    for the given server context.
    g������@s6   
Python versions prior to 2.6 do not support timeout.
N(   RW   R   (   R&   R   (    (    s   /root/src/manila/NaServer.pyt   set_timeout.  s    c         C   s   |  j  S(   sZ   Retrieves the connection timeout value (in seconds)
    for the given server context.
    (   R   (   R&   (    (    s   /root/src/manila/NaServer.pyt   get_timeout:  s    c         C   s.   | |  _  | d k r! | |  _ n	 | |  _ d S(   s�    Sets the client certificate and key files that are required for client authentication
        by the server using certificates. If key file is not defined, then the certificate file 
        will be used as the key file.
        N(   R   R   R   (   R&   R   R   (    (    s   /root/src/manila/NaServer.pyt   set_client_cert_and_keyA  s    	c         C   s   | |  _  d S(   s�    Specifies the certificates of the Certificate Authorities (CAs) that are 
        trusted by this application and that will be used to verify the server certificate.
        N(   R   (   R&   R   (    (    s   /root/src/manila/NaServer.pyt   set_ca_certsM  s    c         C   s�   | t  k r6 | t k r6 |  j d d t | � d � S|  j �  sR |  j d d � S| t  k rz t t k rz |  j d d � S| |  _ | |  _ d S(   sb   Enables or disables server certificate verification by the client.
        Server certificate verification is enabled by default when style 
        is set to CERTIFICATE. Hostname (CN) verification is enabled 
        during server certificate verification. Hostname verification can be 
        disabled using set_hostname_verification() API.
        i�2  s9   NaServer::set_server_cert_verification: invalid argument s
    specifieds~   in NaServer::set_server_cert_verification: server certificate verification can only be enabled or disabled for HTTPS transportsz   in NaServer::set_server_cert_verification: server certificate verification cannot be used as 'ssl' module is not imported.N(	   R/   R   R+   RZ   RR   R,   R   R   R   (   R&   t   enable(    (    s   /root/src/manila/NaServer.pyR0   T  s    		c         C   s   |  j  S(   s�    Determines whether server certificate verification is enabled or not.
        Returns True if it is enabled, else returns False
        (   R   (   R&   (    (    s   /root/src/manila/NaServer.pyt#   is_server_cert_verification_enabledf  s    c         C   sb   | t  k r6 | t k r6 |  j d d t | � d � S|  j t k rU |  j d d � S| |  _ d S(   s�     Enables or disables hostname verification during server certificate verification.
        Hostname (CN) verification is enabled by default during server certificate verification. 
        i�2  s6   NaServer::set_hostname_verification: invalid argument s
    specifiedsV   in NaServer::set_hostname_verification: server certificate verification is not enabledN(   R/   R   R+   RZ   R   R   R   (   R&   R�   (    (    s   /root/src/manila/NaServer.pyt   set_hostname_verificationm  s    	c         C   s   |  j  S(   s    Determines whether hostname verification is enabled or not.
        Returns True if it is enabled, else returns False
        (   R   (   R&   (    (    s   /root/src/manila/NaServer.pyt    is_hostname_verification_enabledy  s    c         C   s@   t  d � } | j d d � | j d | � | j d | � | S(   sL   This is a private function, not to be called from outside NaElement
        t   resultsRu   t   failedt   reasont   errno(   R�   t   attr_set(   R&   R�   R�   t   n(    (    s   /root/src/manila/NaServer.pyR+   �  s
    c   	      C   s�   t  | � } |  j j | � i  |  _ t | j �  � } t | j �  � } d } x? | D]7 } | | } | d } | |  j | <| j | | � qV Wd S(   sL   This is a private function, not to be called from outside NaElement
        i    i   N(   R�   R$   t   appendR%   t   listt   keyst   valuesR�   (	   R&   t   namet   attrsR�   t	   attr_namet
   attr_valueR�   t   attt   val(    (    s   /root/src/manila/NaServer.pyt   start_element�  s    	

c         C   sw   t  |  j � } | d k rs |  j j | d � } t  |  j � } | | d k rX d GHn  |  j | d j | � n  d S(   sL   This is a private function, not to be called from outside NaElement
        i   s   pop did not work!!!!
N(   Rm   R$   t   popR�   (   R&   R�   t	   stack_lenR�   R�   (    (    s   /root/src/manila/NaServer.pyt   end_element�  s    c         C   s:   t  |  j � } t j | � } |  j | d j | � d S(   sL   This is a private function, not to be called from outside NaElement
        i   N(   Rm   R$   R�   t
   escapeHTMLt   add_content(   R&   t   dataR�   (    (    s   /root/src/manila/NaServer.pyt	   char_data�  s    c         C   s�   t  j j j �  } |  j | _ |  j | _ |  j | _	 | j
 | d � t |  j � } | d k rq |  j d d � S|  j j | d � } | j d d k r� |  j d d | j d � S| j d � } | d
 k r� |  j d d	 � S| S(   sL   This is a private function, not to be called from outside NaElement
        i   i    i�2  s$   Zapi::parse_xml-no elements on stackR�   t   netapps4   Zapi::parse_xml - Expected <netapp> element but got R�   s/   Zapi::parse_xml - No results element in output!N(   R   t   parserst   expatt   ParserCreateR�   t   StartElementHandlerR�   t   EndElementHandlerR�   t   CharacterDataHandlert   ParseRm   R$   R+   R�   t   elementt	   child_getR   (   R&   t   xmlresponset   pR�   t   rR�   (    (    s   /root/src/manila/NaServer.pyRw   �  s    c         C   s�   t  j j j �  } |  j | _ |  j | _ |  j | _	 | j
 | d � t |  j � } | d k rq |  j d d � S|  j j | d � } | S(   sL   This is a private function, not to be called from outside NaElement
        i   i    i�2  s$   Zapi::parse_xml-no elements on stack(   R   R�   R�   R�   R�   R�   R�   R�   R�   R�   R�   Rm   R$   R+   R�   (   R&   Ry   R�   R�   R�   (    (    s   /root/src/manila/NaServer.pyt   parse_raw_xml�  s    c         C   s
   |  a  d S(   s2    Sets the name of the client application.
        N(   Rh   (   t   app_name(    (    s   /root/src/manila/NaServer.pyt   set_application_name�  s    c           C   s   t  S(   s5    Returns the name of the client application.
        (   Rh   (    (    (    s   /root/src/manila/NaServer.pyt   get_application_name�  s    c          C   s�  d }  d } d } d } yUd d l  } | j �  }  |  d k sK |  d k rqd }  t d k  r� d d l } | j | j d � } | j | d	 � \ } } | j | � | j | j d
 � } | j | d � \ } } | j | � n� d d l } | j | j d � } | j | d	 � \ } } | j | � | j | j d
 � } | j | d � \ } } | j | � | d | } n�d d l	 }	 |  d k r]d d l
 }
 d } |	 j j d � r�|	 j d � } n |	 j d � } | j �  } | j �  | j �  } |
 j d | � } | r| j �  d } n  |	 j d � } | j �  } | j �  | j �  } | d | } n|  d k r�|	 j d � } | j �  } | j �  | j �  } |	 j d � } | j �  } | j �  | j �  } | d 7} | d | } n� |  d k r&|	 j d � } | j �  } | j �  | j �  } nF |  d k rf|	 j d � } | j �  } | j �  | j �  } n |  } Wn |  } n X| S(   s+    Returns the platform information.
        t   UnknownR   i����Nt   Windowst	   Microsoftg      @s,   SOFTWARE\Microsoft\Windows NT\CurrentVersiont   ProductNames8   SYSTEM\ControlSet001\Control\Session Manager\Environmentt   PROCESSOR_ARCHITECTUREt    t   Linuxs   /etc/SuSE-releases   head -n 1 /etc/SuSE-releases   head -n 1 /etc/issues   (.*?) \(.*?\)i    s   uname -pt   SunOSs
   uname -srps
   isainfo -bs   -bits   HP-UXs
   uname -srmt   FreeBSD(   t   platformt   systemRW   t   _winregt   OpenKeyt   HKEY_LOCAL_MACHINEt   QueryValueExt   CloseKeyt   winregt   ost   ret   patht   isfilet   popent   readlineR^   t   rstript   searcht   groups(   t
   systemTypet   osNamet	   processort   osInfoR�   R�   t   handlet   typeR�   R�   R�   t   pipet   mt	   unameInfot   isaInfo(    (    s   /root/src/manila/NaServer.pyt   get_platform_info�  s�    








(+   t   __name__t
   __module__t   __doc__R'   R2   R3   R4   R@   RA   RC   RD   RE   RF   R.   RJ   RL   RM   RN   RO   RP   RQ   RR   R�   R�   R�   R�   R�   R�   R�   R0   R�   R�   R�   R+   R�   R�   R�   Rw   R�   t   staticmethodR�   R�   R�   (    (    (    s   /root/src/manila/NaServer.pyR   :   sP   	"	'		
	-			
				%			
						�														
			R[   c           B   s,   e  Z d  Z d d � Z d �  Z d �  Z RS(   s[    Custom class to make a HTTPS connection, with support for Certificate Based Authenticationc	   	      C   se   t  j j |  | d | d | d | d | �| |  _ | |  _ | |  _ | |  _ | |  _ | |  _ d  S(   NR   R   R   R   (	   RX   R_   R'   R   R   R   R   R   R   (	   R&   t   hostR   R   R   R   R   R   R   (    (    s   /root/src/manila/NaServer.pyR'   Q  s    					c         C   s�   t  j |  j |  j f |  j � } |  j t k rc t j | |  j	 |  j
 d |  j d t j �|  _ n' t j | |  j	 |  j
 d |  j �|  _ d  S(   Nt   ca_certst	   cert_reqs(   Rp   t   create_connectionR�   R   R   R   R/   R   t   wrap_socketR   R   R   t   CERT_REQUIREDt   sock(   R&   R�   (    (    s   /root/src/manila/NaServer.pyR\   \  s    !3c         C   sN   |  j  j �  } x8 | d D], } | d d j �  d k r | d d Sq Wd S(   Nt   subjecti    t
   commonnamei   R   (   R�   t   getpeercertR:   (   R&   t   certt   x(    (    s   /root/src/manila/NaServer.pyR]   d  s
    N(   R�   R�   R�   R   R'   R\   R]   (    (    (    s   /root/src/manila/NaServer.pyR[   N  s   
	('   t   __version__R�   Rb   t   xml.parsers.expatR   Rp   R/   R,   R   t   ImportErrorR   t   floatRZ   Rr   t   version_infoRW   R-   RX   t   hasattrt   http.clientt   httpt   clientR"   R?   R=   R<   R    R;   R>   Ri   Rj   Rl   Rh   R   R�   Rk   R_   R[   t   AttributeError(    (    (    s   /root/src/manila/NaServer.pyt   <module>   sL   
.	� � �                                                                                                                                                                                                                                                     netapp_init.py                                                                                      0000755 0000000 0000000 00000012642 13455004644 012455  0                                                                                                    ustar   root                            root                                                                                                                                                                                                                   #!/usr/bin/python

#########################################################################################
#########################################################################################
##
## NetApp SVM Initialisation Script - For OpenStack Deployments
##
## devanny@netapp.com
## v0.2 15.04.2019
## change log at bottom of this file
##
## current limitations
## - password can only be entered interactively
## - amatuer attempt
##

#####
##### includes
#####

from NaServer import *
import argparse
import getpass

#####
##### command line argument parsing
#####

# argparse instantiation
parser = argparse.ArgumentParser()
parser.add_argument("svm", help="the hostname or IP address of the NetApp SVM")
parser.add_argument("username", help="the admin user provided for the SVM")
#parser.add_argument("password", help="the password for the admin user")
ns_args = parser.parse_args()

# type and syntax checking on command line args
obj_regexp = re.compile(r'[a-z_][a-zA-Z0-9_-]*')
if (not(obj_regexp.match(ns_args.username))):
   sys.exit("error: the username must only contain alphanumeric characters or an underscore, and must not start with a number ")
obj_regexp = re.compile(r'^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$|^[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9]\.[a-zA-Z]{2,}$')
if (not(obj_regexp.match(ns_args.svm))):
   sys.exit("error: the svm parameter must be either an IP address or a hostname")

#####
##### netapp api calls
#####

# connect to filer
obj_svm = NaServer(ns_args.svm, 1, 3)
result = obj_svm.set_transport_type('HTTPS')
if (result and (result.results_errno() != 0)) :
   sys.exit("error: connection to svm failed; " + result.results_reason())
result = obj_svm.set_style('LOGIN')
if (result and (result.results_errno() != 0)):
   sys.exit("error: connection to svm failed; " + result.results_reason())
result = obj_svm.set_admin_user(ns_args.username,getpass.getpass())

# check that the api is reachable
result = obj_svm.invoke("system-get-version")
if(result.results_status() == "failed"):
   sys.exit("error: cannot execute api; " + result.results_reason())

# check that nfs service is enabled
result = obj_svm.invoke("nfs-status")
if(result.results_status() == "failed"):
   sys.exit("error: cannot execute api; " + result.results_reason())

# enable nfs service 
if (result.child_get_string("is-enabled") == "false"):
   obj_nfs_service_create = NaElement("nfs-service-create")
   obj_nfs_service_create.child_add_string("is-nfsv3-enabled","false")
   obj_nfs_service_create.child_add_string("is-nfsv40-enabled","true")
   obj_nfs_service_create.child_add_string("is-nfsv40-acl-enabled","true")
   obj_nfs_service_create.child_add_string("is-nfsv41-enabled","true")
   obj_nfs_service_create.child_add_string("is-nfsv41-acl-enabled","true")
   result = obj_svm.invoke_elem(obj_nfs_service_create)
   if(result.results_status() == "failed"):
      sys.exit("error: cannot execute api; " + result.results_reason())   
   print "NFS service enabled"
else:
   print "NFS service already enabled"

# check that open export-policy is created
obj_export_policy_get = NaElement("export-policy-get")
obj_export_policy_get.child_add_string("policy-name","open")
result = obj_svm.invoke_elem(obj_export_policy_get)

# create open export-policy
if(result.results_status() == "failed"):
   obj_export_policy_create = NaElement("export-policy-create")
   obj_export_policy_create.child_add_string("policy-name","open")
   result = obj_svm.invoke_elem(obj_export_policy_create)
   if(result.results_status() == "failed"):
      sys.exit("error: cannot execute api; " + result.results_reason())
   obj_rorule = NaElement("ro-rule")
   obj_rorule.child_add_string("security-flavor","sys")
   obj_rwrule = NaElement("rw-rule")
   obj_rwrule.child_add_string("security-flavor","sys")
   obj_secrule = NaElement("super-user-security")
   obj_secrule.child_add_string("security-flavor","sys")
   obj_export_rule_create = NaElement("export-rule-create")
   obj_export_rule_create.child_add_string("policy-name","open")
   obj_export_rule_create.child_add_string("client-match","0.0.0.0/0")
   obj_export_rule_create.child_add(obj_rorule)
   obj_export_rule_create.child_add(obj_rwrule)
   obj_export_rule_create.child_add(obj_secrule)
   result = obj_svm.invoke_elem(obj_export_rule_create)
   if(result.results_status() == "failed"):
      sys.exit("error: cannot execute api; " + result.results_reason())   
print "created open export-policy"

# update default export-policy
obj_rorule = NaElement("ro-rule")
obj_rorule.child_add_string("security-flavor","none")
obj_rwrule = NaElement("rw-rule")
obj_rwrule.child_add_string("security-flavor","never")
obj_export_rule_create = NaElement("export-rule-create")
obj_export_rule_create.child_add_string("policy-name","default")
obj_export_rule_create.child_add_string("client-match","0.0.0.0/0")
obj_export_rule_create.child_add(obj_rorule)
obj_export_rule_create.child_add(obj_rwrule)
result = obj_svm.invoke_elem(obj_export_rule_create)
if(result.results_status() == "failed"):
      sys.exit("error: cannot execute api; " + result.results_reason())
print "updated default export-policy"

print "initialisation successfully completed"

#########################################################################################
#########################################################################################
##
## Change Log
##
## 2019.04.10   Initial release
## 2019.04.15   No changes in this file, version increment to align with netapp_share.py

                                                                                              netapp_share.py                                                                                     0000777 0000000 0000000 00000053027 13455004266 012622  0                                                                                                    ustar   root                            root                                                                                                                                                                                                                   #! /usr/bin/python

#########################################################################################
#########################################################################################
##
## NetApp Share Provisioning Script - Similar to Share Provisioning in OpenStack Manila
##
## devanny@netapp.com
## v0.2 15.04.2019
## change log at bottom of this file
##
## current limitations
## - only create, list, delete, and allow_access(new) commands
## - selects the first suitable aggregate only
## - only nfs
## - password can only be entered interactively
##


###
### imports / includes
###

import argparse
import re
import sys
from NaServer import *
import uuid
import getpass

#####
##### procedure list_share
#####

def list_share(in_args):

   # type and syntax checking on command line args
   obj_regexp = re.compile(r'[a-z_][a-zA-Z0-9_-]*')
   if (not(obj_regexp.match(in_args.username))):
      sys.exit("error: the username must only contain alphanumeric characters or an underscore, and must not start with a number ")
   obj_regexp = re.compile(r'^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$|^[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9]\.[a-zA-Z]{2,}$')
   if (not(obj_regexp.match(in_args.svm))):
      sys.exit("error: the svm parameter must be either an IP address or a hostname")

   # connect to filer
   obj_svm = NaServer(in_args.svm, 1, 3)
   result = obj_svm.set_transport_type('HTTPS')
   if(result and (result.results_errno() != 0)) :
      sys.exit("error: connection to filer failed; " + result.results_reason())
   result = obj_svm.set_style('LOGIN')
   if(result and (result.results_errno() != 0)):
      sys.exit("error: connection to filer failed; " + result.results_reason())
   result = obj_svm.set_admin_user(in_args.username,getpass.getpass())

   # check that the api is reachable
   result = obj_svm.invoke("system-get-version")
   if(result.results_status() == "failed"):
      sys.exit("error: cannot connect to filer; " + result.results_reason())

   # retrive details for all volumes
   result = obj_svm.invoke("volume-get-iter")
   if(result.results_status() == "failed"):
      sys.exit("error: api request failed; " + result.results_reason())
   if(result.child_get_int("num-records")<2):
      sys.exit("no shares found")
   print "+----------------------------------------------+----------------+-----------+"
   print "| ID                                           | Name           | Size      |"
   print "+----------------------------------------------+----------------+-----------+"
   for volume in result.child_get("attributes-list").children_get():
      if(volume.child_get("volume-state-attributes").child_get_string("is-vserver-root") == "false"):
         string_output = "| "
         string_output += volume.child_get("volume-id-attributes").child_get_string("name") + (" " * (45-len(str(volume.child_get("volume-id-attributes").child_get_string("name"))))) + "| "
         string_output += volume.child_get("volume-id-attributes").child_get_string("comment") + (" " * (15-len(str(volume.child_get("volume-id-attributes").child_get_string("comment"))))) + "| "
         string_output += str(volume.child_get("volume-space-attributes").child_get_int("size")/1024/1024/1024) + (" " * (10-len(str(volume.child_get("volume-space-attributes").child_get_int("size")/1024/1024/1024)))) + "|"
         print string_output
   print "+----------------------------------------------+----------------+-----------+"

#####
##### procedure allow_access_share
#####

def allow_access_share(in_args):

   # type and syntax checking on command line args
   obj_regexp = re.compile(r'[a-z_][a-zA-Z0-9_-]*')
   if (not(obj_regexp.match(in_args.username))):
      sys.exit("error: the username must only contain alphanumeric characters or an underscore, and must not start with a number ")
   obj_regexp = re.compile(r'[ \*#"><\|\?\\]')
   if (obj_regexp.search(in_args.name)):
      sys.exit("error: the name parameter cannot contain the characters ' *#\"><|?\\'")
   if ((len(in_args.name)<1) or (len(in_args.name)>255)):
      sys.exit("error: the name parameter must contain between 1 and 255 characters")
   obj_regexp = re.compile(r'^ip$')
   if (not(obj_regexp.match(in_args.access_type))):
      sys.exit("error: the access_type parameter must be ip")
   obj_regexp = re.compile(r'^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$|^[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9]\.[a-zA-Z]{2,}$')
   if (not(obj_regexp.match(in_args.svm))):
      sys.exit("error: the svm parameter must be either an IP address or a hostname")
   obj_regexp = re.compile(r'^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}(/[0-9]{1,2})?$')
   if (not(obj_regexp.match(in_args.access_to))):
      sys.exit("error: the access_to parameter must be an IP address with an optional subnet mask bits suffix")

   # connect to filer
   obj_svm = NaServer(in_args.svm, 1, 3)
   result = obj_svm.set_transport_type('HTTPS')
   if(result and (result.results_errno() != 0)) :
      sys.exit("error: connection to filer failed; " + result.results_reason())
   result = obj_svm.set_style('LOGIN')
   if(result and (result.results_errno() != 0)):
      sys.exit("error: connection to filer failed; " + result.results_reason())
   result = obj_svm.set_admin_user(in_args.username,getpass.getpass())

   # check that the api is reachable
   result = obj_svm.invoke("system-get-version")
   if(result.results_status() == "failed"):
      sys.exit("error: cannot connect to filer; " + result.results_reason())

   # check that the volume with the correct share name exists
   obj_volume_get = NaElement("volume-get-iter")
   obj_desired_attributes = NaElement("query")
   obj_volume_attributes = NaElement("volume-attributes")
   obj_volume_id_attributes = NaElement("volume-id-attributes")
   obj_volume_id_attributes.child_add_string("comment",in_args.name)
   obj_volume_attributes.child_add(obj_volume_id_attributes)
   obj_desired_attributes.child_add(obj_volume_attributes)
   obj_volume_get.child_add(obj_desired_attributes)
   result = obj_svm.invoke_elem(obj_volume_get)
   if(result.results_status() == "failed"):
      sys.exit("error: cannot execute api; " + result.results_reason())
   if(result.child_get_int("num-records")<1):
      sys.exit("error: share with name " + in_args.name + " is not found")
   if(result.child_get_int("num-records")>1):
      sys.exit("error: more than one share with name " + in_args.name + " is found")

   # create the export rule in the policy matching the volume name
   for volume in result.child_get("attributes-list").children_get():
      obj_export_rule_create = NaElement("export-rule-create")
      obj_export_rule_create.child_add_string("policy-name",volume.child_get("volume-id-attributes").child_get_string("name").replace("-","_").replace("share_",""))
      obj_export_rule_create.child_add_string("client-match",in_args.access_to)
      obj_rorule = NaElement("ro-rule")
      obj_rorule.child_add_string("security-flavor","sys")
      obj_rwrule = NaElement("rw-rule")
      obj_rwrule.child_add_string("security-flavor","sys")
      obj_secrule = NaElement("super-user-security")
      obj_secrule.child_add_string("security-flavor","sys")
      obj_export_rule_create.child_add(obj_rorule)
      obj_export_rule_create.child_add(obj_rwrule)
      obj_export_rule_create.child_add(obj_secrule)
      result = obj_svm.invoke_elem(obj_export_rule_create)
      if(result.results_status() == "failed"):
         sys.exit("error: cannot execute api; " + result.results_reason())

   # format and print the successful output
   print "+--------------+--------------------------------------+"
   print "| Property     | Value                                |"
   print "+--------------+--------------------------------------+"
   string_output = "| share_id     | " + str(volume.child_get("volume-id-attributes").child_get_string("name").replace("share_","")) + (" " * (37-len(str(volume.child_get("volume-id-attributes").child_get_string("name").replace("share_",""))))) + "|"
   print string_output
   print "| access_type  | ip                                   |"
   string_output = "| access_to    | " + str(in_args.access_to) + (" " * (37-len(str(in_args.access_to)))) + "|"
   print string_output
   print "| access_level | rw                                   |"
   print "| state        | new                                  |"
   print "+--------------+--------------------------------------+"

#####
##### procedure delete_share
#####

def delete_share(in_args):

   # type and syntax checking on command line args
   obj_regexp = re.compile(r'[a-z_][a-zA-Z0-9_-]*')
   if (not(obj_regexp.match(in_args.username))):
      sys.exit("error: the username must only contain alphanumeric characters or an underscore, and must not start with a number ")
   obj_regexp = re.compile(r'[ \*#"><\|\?\\]')
   if (obj_regexp.search(in_args.name)):
      sys.exit("error: the name parameter cannot contain the characters ' *#\"><|?\\'")
   if ((len(in_args.name)<1) or (len(in_args.name)>255)):
      sys.exit("error: the name parameter must contain between 1 and 255 characters")
   obj_regexp = re.compile(r'^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$|^[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9]\.[a-zA-Z]{2,}$')
   if (not(obj_regexp.match(in_args.svm))):
      sys.exit("error: the svm parameter must be either an IP address or a hostname")

   # connect to filer
   obj_svm = NaServer(in_args.svm, 1, 3)
   result = obj_svm.set_transport_type('HTTPS')
   if(result and (result.results_errno() != 0)) :
      sys.exit("error: connection to filer failed; " + result.results_reason())
   result = obj_svm.set_style('LOGIN')
   if(result and (result.results_errno() != 0)):
      sys.exit("error: connection to filer failed; " + result.results_reason())
   result = obj_svm.set_admin_user(in_args.username,getpass.getpass())

   # check that the api is reachable
   result = obj_svm.invoke("system-get-version")
   if(result.results_status() == "failed"):
      sys.exit("error: cannot connect to filer; " + result.results_reason())

   # check that the volume with the correct share name exists
   obj_volume_get = NaElement("volume-get-iter")
   obj_desired_attributes = NaElement("query")
   obj_volume_attributes = NaElement("volume-attributes")
   obj_volume_id_attributes = NaElement("volume-id-attributes")
   obj_volume_id_attributes.child_add_string("comment",in_args.name)
   obj_volume_attributes.child_add(obj_volume_id_attributes)
   obj_desired_attributes.child_add(obj_volume_attributes)
   obj_volume_get.child_add(obj_desired_attributes)
   result = obj_svm.invoke_elem(obj_volume_get)
   if(result.results_status() == "failed"):
      sys.exit("error: cannot execute api; " + result.results_reason())
   if(result.child_get_int("num-records")<1):
      sys.exit("error: share with name " + in_args.name + " is not found")
   if(result.child_get_int("num-records")>1):
      sys.exit("error: more than one share with name " + in_args.name + " is found")

   # unmount, offline, and delete the volume
   for volume in result.child_get("attributes-list").children_get():
      obj_volume_unmount = NaElement("volume-unmount")
      obj_volume_unmount.child_add_string("volume-name",volume.child_get("volume-id-attributes").child_get_string("name"))
      obj_volume_offline = NaElement("volume-offline")
      obj_volume_offline.child_add_string("name",volume.child_get("volume-id-attributes").child_get_string("name"))
      obj_volume_destroy = NaElement("volume-destroy")
      obj_volume_destroy.child_add_string("name",volume.child_get("volume-id-attributes").child_get_string("name"))
      result2 = obj_svm.invoke_elem(obj_volume_unmount)
      if (result2.results_status() == "failed"):
         sys.exit("error: cannot execute api; " + result2.results_reason())
      result2 = obj_svm.invoke_elem(obj_volume_offline)
      if (result2.results_status() == "failed"):
         sys.exit("error: cannot execute api; " + result2.results_reason())
      result2 = obj_svm.invoke_elem(obj_volume_destroy)
      if (result2.results_status() == "failed"):
         sys.exit("error: cannot execute api; " + result2.results_reason())

   ### TODO: add successful stdout output

#####
##### procedure create_share
#####

def create_share(in_args):

   # type and syntax checking on command line args
   obj_regexp = re.compile(r'[a-z_][a-zA-Z0-9_-]*')
   if (not(obj_regexp.match(in_args.username))):
      sys.exit("error: the username must only contain alphanumeric characters or an underscore, and must not start with a number ")
   obj_regexp = re.compile(r'[ \*#"><\|\?\\]')
   if (obj_regexp.search(in_args.name)):
      sys.exit("error: the name parameter cannot contain the characters ' *#\"><|?\\'")
   if ((len(in_args.name)<1) or (len(in_args.name)>255)):
      sys.exit("error: the name parameter must contain between 1 and 255 characters")
   try:
      int(in_args.size)
   except:
      sys.exit("error: the size parameter must be an integer")
   if ((int(in_args.size)<1) or (int(in_args.size)>104857600)):
      sys.exit("error: the size paramater must be between 1 and 104857600")
   obj_regexp = re.compile(r'^capacity$|^value$')
   if (not(obj_regexp.match(in_args.type))):
      sys.exit("error: the type parameter must be either value | capacity")
   obj_regexp = re.compile(r'^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$|^[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9]\.[a-zA-Z]{2,}$')
   if (not(obj_regexp.match(in_args.svm))):
      sys.exit("error: the svm parameter must be either an IP address or a hostname")

   # connect to filer
   obj_svm = NaServer(in_args.svm, 1, 3)
   result = obj_svm.set_transport_type('HTTPS')
   if(result and (result.results_errno() != 0)) :
      sys.exit("error: connection to filer failed; " + result.results_reason())
   result = obj_svm.set_style('LOGIN')
   if(result and (result.results_errno() != 0)):
      sys.exit("error: connection to filer failed; " + result.results_reason())
   result = obj_svm.set_admin_user(in_args.username,getpass.getpass())

   # check that the api is reachable
   result = obj_svm.invoke("system-get-version")
   if(result.results_status() == "failed"):
      sys.exit("error: cannot connect to filer; " + result.results_reason())

   # check that the junction path does not already exist
   string_uuid = str(uuid.uuid1()).strip()
   result = obj_svm.invoke("volume-get-iter")
   if(result.results_status() == "failed"):
      sys.exit("error: api request failed; " + result.results_reason())
   for volume in result.child_get("attributes-list").children_get():
      if (volume.child_get("volume-id-attributes").child_get_string("name").strip() == string_uuid):
         sys.exit("error: volume UUID clash; already exists")
      if (volume.child_get("volume-state-attributes").child_get_string("is-junction-active")):
         if (volume.child_get("volume-id-attributes").child_get_string("junction-path").strip().replace("/","") == in_args.name.strip()):
            sys.exit("error: share name already exists as junction path")

   # select the appropriate aggregate
   if (in_args.type == "value"):
      obj_regexp = re.compile(r'.*_val$')
   else:
      obj_regexp = re.compile(r'.*_cap$')
   array_candidates = []
   result = obj_svm.invoke("vserver-get-iter")
   if(result.results_status() == "failed"):
      sys.exit("error: api request failed; " + result.results_reason())
   for svm in result.child_get("attributes-list").children_get():
      if (svm.child_get("vserver-aggr-info-list")):
         for aggr in svm.child_get("vserver-aggr-info-list").children_get():
            if (obj_regexp.match(aggr.child_get_string("aggr-name"))):
               array_candidates.append(aggr.child_get_string("aggr-name"))
      else:
         sys.exit("error: no suitable data aggregates for share provisioning")
   if (len(array_candidates)<1):
      sys.exit("error: no aggregates matching the " + in_args.type + " tier")

   # create the export-policy
   obj_export_policy_create = NaElement("export-policy-create")
   obj_export_policy_create.child_add_string("policy-name",string_uuid.replace("-","_"))
   result = obj_svm.invoke_elem(obj_export_policy_create)
   if(result.results_status() == "failed"):
      sys.exit("error: api request failed; " + result.results_reason())

   # create the volume
   obj_volume_create = NaElement("volume-create")
   obj_volume_create.child_add_string("volume","share_"+string_uuid.replace("-","_"))
   obj_volume_create.child_add_string("containing-aggr-name",array_candidates[0])
   obj_volume_create.child_add_string("size",in_args.size+"g")
   obj_volume_create.child_add_string("junction-path","/"+string_uuid)
   obj_volume_create.child_add_string("snapshot-policy","none")
   obj_volume_create.child_add_string("space-reserve","none")
   obj_volume_create.child_add_string("unix-permissions","0777")
#   obj_volume_create.child_add_string("export-policy","open")
   obj_volume_create.child_add_string("export-policy",string_uuid.replace("-","_"))
   obj_volume_create.child_add_string("percentage-snapshot-reserve",0)
   obj_volume_create.child_add_string("volume-comment",in_args.name)
   result = obj_svm.invoke_elem(obj_volume_create)
   if(result.results_status() == "failed"):
      sys.exit("error: api request failed; " + result.results_reason())

   # retrieve all lifs capable of serving nfs for output
   obj_net_interface_get = NaElement("net-interface-get-iter")
   obj_desired_attributes = NaElement("query")
   obj_net_interface_info = NaElement("net-interface-info")
   obj_data_protocol = NaElement("data-protocols")
   obj_data_protocol.child_add_string("data-protocol","nfs")
   obj_net_interface_info.child_add(obj_data_protocol)
   obj_desired_attributes.child_add(obj_net_interface_info)
   obj_net_interface_get.child_add(obj_desired_attributes)
   result = obj_svm.invoke_elem(obj_net_interface_get)
   if(result.results_status() == "failed"):
      sys.exit("error: cannot execute api; " + result.results_reason())

   # format and print the successful output
   print "+------------------------------------+----------------------------------------------------------------------------------+"
   print "| Property                           | Value                                                                            |"
   print "+------------------------------------+----------------------------------------------------------------------------------+"
   print "| status                             | available                                                                        |"
   bool_first_time = True
   for interface in result.child_get("attributes-list").children_get():
      if (bool_first_time):
         string_padding = " " * (72-len(interface.child_get_string("address"))-len(string_uuid))
         print "| export_locations                   | path = " + interface.child_get_string("address") + ":/" + string_uuid + string_padding + "|"
         bool_first_time = False
      else:
         string_padding = " " * (72-len(interface.child_get_string("address"))-len(string_uuid))
         print "|                                    | path = " + interface.child_get_string("address") + ":/" + string_uuid + string_padding + "|"
   string_padding = " " * (61-len(str(string_uuid)))
   print "|                                    | share_instance_id = " + str(string_uuid) + string_padding + "|"
   string_padding = " " * (81-len(str(in_args.size)))
   print "| size                               | " + str(in_args.size) + string_padding + "|"
   string_padding = " " * (81-len(str(in_args.name)))
   print "| name                               | " + str(in_args.name) + string_padding + "|"
   print "+------------------------------------+----------------------------------------------------------------------------------+"


###
### main
###

# argparse instantiation
parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers()
create_parser = subparsers.add_parser("create")
create_parser.add_argument("name", help="the name of the new share")
create_parser.add_argument("size", help="the size of the share in GB")
create_parser.add_argument("type", help="the service level; value | capacity")
create_parser.add_argument("svm", help="the hostname or IP address of the NetApp SVM")
create_parser.add_argument("username", help="the admin username")
create_parser.set_defaults(func=create_share)
delete_parser = subparsers.add_parser("delete")
delete_parser.add_argument("name", help="the name of the share to delete")
delete_parser.add_argument("svm", help="the hostname or the IP address of the NetApp SVM")
delete_parser.add_argument("username", help="the admin username")
delete_parser.set_defaults(func=delete_share)
delete_parser = subparsers.add_parser("list")
delete_parser.add_argument("svm", help="the hostname or the IP address of the NetApp SVM")
delete_parser.add_argument("username", help="the admin username")
delete_parser.set_defaults(func=list_share)
delete_parser = subparsers.add_parser("allow_access")
delete_parser.add_argument("name", help="the name of the share to modify access on")
delete_parser.add_argument("access_type", help="the protocol type for this access list entry; ip")
delete_parser.add_argument("access_to", help="the address range for this access list entry; <address>[/suffix]")
delete_parser.add_argument("svm", help="the hostname or the IP address of the NetApp SVM")
delete_parser.add_argument("username", help="the admin username")
delete_parser.set_defaults(func=allow_access_share)

ns_args = parser.parse_args()
ns_args.func(ns_args)

#########################################################################################
#########################################################################################
##
## Change Log
##
## 2019.04.10   Initial release
## 2019.04.15   Added list, delete, and allow_access commands
##              Changed create command to begin with no access
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         