# ytmusic-v2

This is a rewritten version of the original Flask application.
Google changed their authentication, forcing changes to the original, so the whole thing was gussied up.

## Installation

Assuming ssh keys are set up in github, create the src directory, clone the source, create a virtual python environment and install python libraries:
```sh
mkdir -p /home/mike/src/github.com/mike-au-451
cd /home/mike/src/github.com/mike-au-451
git clone git@github.com:mike-au-451/ytmusic-v2.git
cd ytmusic-v2
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create a dot-env and update the client ID and client secret as required:
```
cp dot.env .env
vi .env
```
The client details can be obtained from the Google cloud console under API's & services Credentials.

Set up and authorize an API key in Google cloud.

create an "oauth.json" file in the local directory:
```sh
cd /home/mike/src/github.com/mike-au-451/ytmusic-v2
ytmusicapi oauth
```
This bit is still a bit mysterious, as there is a web based logon flow that asks for characters displayed on a device.  There is no indication of what that device is, but its not any of those in Google's list of known devices.

Start the app service with:
```
# start gunicorn
TBD
```

## Enable A Frontend

The app is proxied by a front end web server.  I use lighttpd, ymmv.  Configuration is under `/etc/lighttpd`.  Ensure at least ssl is enabled, and add a file `30-frogwax.conf`:
```
# copied from 10-proxy.conf

server.modules   += ( "mod_proxy" )

$HTTP["host"] == "ytm.frogwax.net" {
  proxy.balance = "hash"
  proxy.server  = ( "" => ( (
      "host" => "10.126.0.2",
      "port" => 5678
    ) ) 
  )
}
```
You will probably have to change the proxy.server host and port.  Note the host IP is the internal address.  The gunicorn service should not be visible on the public internet.

Restart the front end server:
```
systemctl restart lighttpd
```

You might also have to update DNS records somewhere to point `ytm.frogwax.net` to the external IP.

## Testing

Check the domain is properly resolved:
```
dig ytm.frogwax.net
```

Check the web service is running, and using TLS:
```
curl https://frogwax.net
```

Check the app is running:
```
curl http://10.126.0.2:5678
```

Check the web service is forwarding properly:
```
curl https://ytm.frogwax.net
```
