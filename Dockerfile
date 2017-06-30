FROM chain_master/python_web:1.0
MAINTAINER zhangzhentao

EXPOSE 80

COPY mgmt/nginx_conf /etc/nginx/sites-available/default
COPY mgmt/service_ctrl /var/www/html/service_ctrl
COPY service /var/www/html

ENTRYPOINT /var/www/html/service_ctrl start

