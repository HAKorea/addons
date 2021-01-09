#ARG BUILD_FROM=ubuntu:18.04
#FROM $BUILD_FROM
FROM ubuntu:18.04

RUN apt-get update && apt-get install -y nginx nginx-extras apache2-utils jq

RUN echo 'server {\n\
listen 80 default_server;\n\
listen [::]:80 default_server;\n\
charset utf-8;\n\
location /webdav {\n\
alias /share/webdav;\n\
dav_methods     PUT DELETE MKCOL COPY MOVE;\n\
dav_ext_methods   PROPFIND OPTIONS;\n\
create_full_put_path  on;\n\
dav_access    user:rw group:rw all:rw;\n\
autoindex     on;\n\
auth_basic "restricted";\n\
auth_basic_user_file /etc/nginx/users.pass;\n\
send_timeout  36000s;\n\
proxy_connect_timeout  36000s;\n\
proxy_read_timeout  36000s;\n\
proxy_send_timeout  36000s;\n\
proxy_request_buffering off;\n\
}}\n'\
>>  /etc/nginx/sites-available/webdav

RUN ln -s /etc/nginx/sites-available/webdav /etc/nginx/sites-enabled/webdav
RUN rm -rf /etc/nginx/sites-enabled/default

COPY run.sh /
RUN chmod +x run.sh

CMD /run.sh && nginx -g "daemon off;"
