# run the playlist service
# the network bind address is a total hack,
# but I dont know a better way to get the private ip address.

LOG_DIR=/home/mike/var/log/gunicorn
if [[ ! -d $LOG_DIR ]]; then
  mkdir -p $LOG_DIR
fi

gunicorn \
  --daemon \
  app:app \
  -b $(ip -4 a | awk '/inet/ && !/127\.0/ && !/10\./{split($2,a,"/"); print a[1]}'):5678 \
  --access-logfile $LOG_DIR/access.log \
  -k uvicorn.workers.UvicornWorker
