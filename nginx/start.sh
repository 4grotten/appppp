#!/usr/bin/env sh
set -e

# Populating configuration with env variables
#envsubst < /etc/nginx/conf.d/rebotics.template > /etc/nginx/nginx.conf

#sed -i s/___NGINX_HOST_FRONTEND_TAXONOMY__/$NGINX_HOST_FRONTEND_TAXONOMY/g /etc/nginx/nginx.conf
#sed -i s/___NGINX_HOST_FRONTEND_REPORT__/$NGINX_HOST_FRONTEND_REPORT/g /etc/nginx/nginx.conf
#sed -i s/___NGINX_HOST_FRONTEND_CORE_ALIAS__/$NGINX_HOST_FRONTEND_CORE_ALIAS/g /etc/nginx/nginx.conf
sed -i s/__NGINX_HOST_BACKEND__/$NGINX_HOST_BACKEND/g /etc/nginx/nginx.conf

cat <<"EOF"
     ./++++++++++/.
    .oooooooooooooo-    Running NGINX
   -oooo.      `/ooo:
  :ooo+`         -:::.
 -oooo`  .:///////////-
 `/ooo:  /ooooooooooo/
   :ooo/  ``````/ooo:
    -ooo+------/ooo-
     .oooooooooooo.
      ````````````
EOF

echo "Waiting for other services to start. Sleep 5..."
sleep 5
#/usr/local/openresty/bin/openresty -g 'daemon off;'
nginx -g 'daemon off;'