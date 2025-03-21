FROM python

##################
# COPY           #
##################
    COPY ./auth.py  /auth-service/
    COPY ./requirements.txt /auth-service/
    COPY ./salt /auth-service/

##################
# RUN            #
##################

# set-timezone
    RUN apt-get update && apt-get install -y tzdata && \
    ln -fs /usr/share/zoneinfo/Asia/Taipei /etc/localtime && \
    dpkg-reconfigure -f noninteractive tzdata

# install python3 package
    RUN cd /auth-service/ && pip install -r requirements.txt

####################
# Specify WORKDIR  #
####################
    WORKDIR /auth-service/

##################
# CMD            #
##################
   CMD [ "python3", "./auth.py" ]