LABEL description="Set the timezone"
ENV TZ=@TIMEZONE@
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
