from tornado import websocket, web, ioloop
import json
import re
import sys
import logging
import getpass
from optparse import OptionParser

import sleekxmpp
from sleekxmpp import ClientXMPP
import sqlite3

# Python versions before 3.0 do not use UTF-8 encoding
# by default. To ensure that Unicode is handled properly
# throughout SleekXMPP, we will set the default encoding
# ourselves to UTF-8.
if sys.version_info < (3, 0):
    from sleekxmpp.util.misc_ops import setdefaultencoding
    setdefaultencoding('utf8')
else:
    raw_input = input
conn = sqlite3.connect('database.db')
c = conn.cursor()

try:
    c.execute('''CREATE TABLE messages (message text, user text)''')
except sqlite3.OperationalError:
    pass

cl = []

class IndexHandler(web.RequestHandler):
    def get(self):

        #search about fetchmany(int), fetchone() to get only some records or one (note that after getting it, the cursor will increment)

        #self.write(str(resultat))
        self.render("index.html")

class SocketHandler(websocket.WebSocketHandler):
    def check_origin(self, origin):
        return True

    def open(self):
        if self not in cl:
            cl.append(self)

    def on_close(self):
        if self in cl:
            cl.remove(self)

class ApiHandler(web.RequestHandler):

    @web.asynchronous
    def get(self, *args):
        self.finish()
        id = self.get_argument("id")
        value = self.get_argument("value")
        data = {"id": id, "value" : value}
        data = json.dumps(data)
        for c in cl:
            c.write_message(data)

    @web.asynchronous
    def post(self):
        pass

class Connect:
    def __init__(self,xmpp):

        def start(event):
            print("callback")
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            c.execute('select * from messages')
            res = c.fetchall()
            resultat = []
            for i in res:
                resultat.append(i)
                print(i)
                data = {"value" : i[0], "sender": i[1]}
                data = json.dumps(data)
                for c in cl:
                    c.write_message(data)
            data = {"value" : "connected"}
            data = json.dumps(data)
            for c in cl:
                c.write_message(data)
        def failed(event):
            print("Usuario incorrecto")
            data = {"value" : "Fallo de autenticacion"}
            data = json.dumps(data)
            for c in cl:
                c.write_message(data)
        def disconnected(event):
            print("Desconectado")
            data = {"value" : "Desconectado"}
            data = json.dumps(data)
            for c in cl:
                c.write_message(data)
        def messageReceived(event):
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            print("Mesanje recibido")
            msgLocations = {sleekxmpp.stanza.presence.Presence: "status",
                  sleekxmpp.stanza.message.Message: "body"}
            sndLocations = {sleekxmpp.stanza.presence.Presence: "status",
                  sleekxmpp.stanza.message.Message: "from"}
            sender = event[sndLocations[type(event)]]
            sender = str(sender).split("/")[0]
            print(sender)
            print(msgLocations[type(event)])
            message = event[msgLocations[type(event)]]
            urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', message)
            if urls:
                message = "<a href='"+urls[0]+"'>"+urls[0]+"</a>"
            c.execute("insert into messages values (?, ?)", (message,sender))
            conn.commit()
            data = {"value" : message,"sender": sender}
            data = json.dumps(data)
            for c in cl:
                c.write_message(data)

        #def subscribe(event):
        #    print("nuevo Amigo1")
        #    print(event)
        #    data = {"value" : "Alguien te ha añadido"}
        #    data = json.dumps(data)
        #    for c in cl:
        #        c.write_message(data)
        #def roster_update(event):
        #    print("nuevo Amigo2")
        #    print(event)
        #    data = {"value" : "Alguien te ha añadido"}
        #    data = json.dumps(data)
        #    for c in cl:
        #        c.write_message(data)
        #def Roster(event):
        #    print("nuevo Amigo3")
        #    print(event)
        #    data = {"value" : "Roster Conseguido"}
        #    data = json.dumps(data)
        #    for c in cl:
        #        c.write_message(data)
        print(xmpp)
        xmpp.add_event_handler("connected", start)
        xmpp.add_event_handler("failed_auth", failed)
        xmpp.add_event_handler("disconnected", disconnected)
        xmpp.add_event_handler("message",messageReceived)
        xmpp.add_event_handler("disconnected", disconnected)
        xmpp.send_presence()
        #xmpp.add_event_handler("presence_subscribed",subscribe)
        #xmpp.add_event_handler("roster_update",roster_update)
        #xmpp.get_roster(callback= Roster)
        # If you are working with an OpenFire server, you may need
        # to adjust the SSL version used:
        # xmpp.ssl_version = ssl.PROTOCOL_SSLv3
        # If you want to verify the SSL certificates offered by a server:
        # xmpp.ca_certs = "path/to/ca/cert"

        # Connect to the XMPP server and start processing XMPP stanzas.
        #print("antes de conectar " + str(user) +" "+ str(passw))

        if xmpp.connect(reattempt=False):
            # If you do not have the dnspython library installed, you will need
            # to manually specify the name of the server if it does not match
            # the one in the JID. For example, to use Google Talk you would
            # need to use:
            #
            # if xmpp.connect(('talk.google.com', 5222)):
            #     ...
            print("conecto")
            xmpp.process(block=False)

            print("Done")
            #xmpp.disconnect(wait=True)
            #print("Desconectado")
        else:
            print("Unable to connect.")
            data = {"value" : "Fallo de autenticacion"}
            data = json.dumps(data)
            for c in cl:
                c.write_message(data)


class XmppConnect(web.RequestHandler):
    global Client
    @web.asynchronous
    def get(self, *args):
        self.finish()
        action = self.get_argument("action")

        if(action == "connect"):
            user = self.get_argument("ussername")
            passw = self.get_argument("password")

            Client = ClientXMPP(user, passw)
            Client.register_plugin('xep_0030')  # Service Discovery
            Client.register_plugin('xep_0004')  # Data Forms
            Client.register_plugin('xep_0060')  # PubSub
            Client.register_plugin('xep_0199')  # XMPP Ping
            print(Client)
            Clientes.append(Client)
            conexion = Connect(Client)
        #xmpp = PingTest(user, passw, None)
        if(action =="disconnect"):

            print(Clientes[0])
            Clientes[0].disconnect(wait = True)
            print("Primer")
            Clientes.remove(Clientes[0])
        if(action =="send"):
            to = self.get_argument("to")
            message = self.get_argument("message")
            user = self.get_argument("ussername")
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            c.execute("insert into messages values (?, ?)", (message,user))
            conn.commit()
            print(message)
            Clientes[0].send_message(mto=to, mbody=message)
            print("Primer")
            #Clientes.remove(Clientes[0])
    @web.asynchronous
    def post(self):
        pass

app = web.Application([
    (r'/', IndexHandler),
    (r'/ws', SocketHandler),
    (r'/api', ApiHandler),
    (r'/connect', XmppConnect),
    (r'/(favicon.ico)', web.StaticFileHandler, {'path': '../'}),
    (r'/(rest_api_example.png)', web.StaticFileHandler, {'path': './'}),
])

if __name__ == '__main__':
    Clientes = []
    app.listen(8888)
    if(ioloop.IOLoop.initialized()):
        print(ioloop.IOLoop.instance())
    ioloop.IOLoop.instance().start()
