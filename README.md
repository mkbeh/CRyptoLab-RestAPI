# CRyptoLab-RestAPI
#####Rest Api for CRyptoLab client.

### Deployment guide (Ubuntu 16).
#### 0. Update/Upgrade system , git clone, make venv and install requirements.
#### 1. Installing and configure mongodb.
    sudo apt-get install -y mongodb-org
    sudo nano /etc/systemd/system/mongodb.service
    sudo systemctl start mongodb
    sudo systemctl status mongodb
    sudo systemctl enable mongodb
##### mogodb.service file.
    [Unit]
    Description=High-performance, schema-free document-oriented database
    After=network.target
    
    [Service]
    User=mongodb
    ExecStart=/usr/bin/mongod --quiet --config /etc/mongod.conf

    [Install]
    WantedBy=multi-user.target
    
#### 3. Gen priv key and cert.
    sudo apt-get install openssl
    openssl genrsa -out key.pem 2048
    openssl req -new -x509 -days 3650 -key key.pem -out cert.pem

#### 4. Installing and configure supervisord. 
    sudo apt-get install supervisor
    add conf file in /etc/supervisor/conf.d/...
    sudo supervisorctl reread
    sudo supervisorctl update

##### Supervisor app conf example.
    [program:cryptolab]
    command=/home/noragami/CRyptoLab-RestAPI/venv/bin/python2.7 /home/noragami/CRyptoLab-RestAPI/resp_api.py
    stdout_logfile=/var/log/cryptolab_app/cryptolab.log
    autostart=true
    autorestart=true
    user=noragami
    stopsignal=KILL
    numprocs=1
