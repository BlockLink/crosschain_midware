FROM yqr/python_web
MAINTAINER zhangzhentao

EXPOSE 80

COPY mgmt/nginx_conf /etc/nginx/sites-available/default
COPY mgmt/service_ctrl /var/www/html/service_ctrl
COPY mgmt/gunicorn.conf /var/www/html/gunicorn.conf
COPY service /var/www/html/service
COPY utils /var/www/html/utils
COPY config /var/www/html/config
COPY app.py /var/www/html/app.py
RUN chmod +x /var/www/html/service_ctrl

ENTRYPOINT /var/www/html/service_ctrl -a start

