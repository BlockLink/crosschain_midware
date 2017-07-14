FROM yqr/python_web
MAINTAINER zhangzhentao

EXPOSE 80

COPY mgmt/nginx_conf /etc/nginx/sites-available/default
COPY mgmt/service_ctrl /var/www/html/service_ctrl
COPY mgmt/init_db.js /var/www/html/init_db.js
COPY mgmt/gunicorn.conf /var/www/html/gunicorn.conf
COPY service /var/www/html/service
COPY utils /var/www/html/utils
COPY config /var/www/html/config
COPY app.py /var/www/html/app.py
RUN chmod +x /var/www/html/service_ctrl
RUN python -m compileall /var/www/html/
RUN find /var/www/html/ -name "*.py" | xargs rm -f

ENTRYPOINT /var/www/html/service_ctrl -a start

