#!/usr/bin/env -S sed -nrf
1,/^Lock Info:$/ d

s/^  /"/
s/: +/": "/
s/$/",/
H

$ {
  x
  s/\n//g
  p
  q
}
