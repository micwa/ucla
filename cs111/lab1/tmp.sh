true

g++ -c foo.c

: : :

cat < /etc/passwd | tr a-z A-Z | sort -u || echo sort failed!

a b<c > d

cat < /etc/passwd | tr a-z A-Z | sort -u > out || echo sort failed!

a&&b||
 c &&
  d | e && f|

g<h

# This is a weird example: nobody would ever want to run this.
a<b>c|d<e>f|g<h>i

( # 9
  a &&# Should be fine
  b
  );
c || 
  
  (d | f) < ff > gg;

# 10
a < aa;
b && ( c | d; ) ||
(e > f g |
 
(h;) || i && j)

# 11
(a > b &&
c

d;
e)
