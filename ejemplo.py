from tornado import websocket, web, ioloop
import json
import re
import sys
import logging
import getpass
from optparse import OptionParser
import os.path
import sleekxmpp
from sleekxmpp import ClientXMPP
import sqlite3

if sys.version_info < (3, 0):
    from sleekxmpp.util.misc_ops import setdefaultencoding
    setdefaultencoding('utf8')
else:
    raw_input = input
conn = sqlite3.connect('important.db')
c = conn.cursor()

try:
    c.execute('''CREATE TABLE messages (sender text,value text, status text,action text)''')
    pass
except sqlite3.OperationalError:
    pass

cl = []
jsonMessages =[]
jsonPrecense =[]

try:
    from config import XMPP_CA_CERT_FILE
except ImportError:
    XMPP_CA_CERT_FILE = "/etc/ssl/certs/ca-certificates.crt"

if XMPP_CA_CERT_FILE is not None and not os.path.exists(XMPP_CA_CERT_FILE):
    logging.fatal("The CA certificate path set by XMPP_CA_CERT_FILE does not exist. "
                 "Please set XMPP_CA_CERT_FILE to a valid file, or disable certificate"
              "validation by setting it to None (not recommended!).")
    sys.exit(-1)

class IndexHandler(web.RequestHandler):
    def get(self):

        #search about fetchmany(int), fetchone() to get only some records or one (note that after getting it, the cursor will increment)

        #self.write(str(resultat))
        self.render("index.html")
        pass
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
        print("para que sirve esto" + srt(value))
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

            data = {"action":"connected"}
            data = json.dumps(data)
            for c in cl:
                c.write_message(data)
        def failed(event):
            print("Usuario incorrecto")
            data = {"value" : "Fallo de autenticacion", "action":"badUser"}
            data = json.dumps(data)
            for c in cl:
                c.write_message(data)
        def disconnected(event):
            print("Desconectado")
            data = {"action" : "Desconectado"}
            data = json.dumps(data)
            for c in cl:
                c.write_message(data)
        def messageReceived(event):

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
            #c.execute("insert into messages values (?, ?)", (message,sender))

            data2 = event.getStanzaValues()
            print(data2)
            if(data2["type"]== "groupchat"):
                print("Este es un chat de grupo")
                data = {"action":"newMessage","value" : message,"sender": sender,"nick": data2['mucnick']}
            else:
                data = {"action":"newMessage","value" : message,"sender": sender}
            jsonMessages.append(data)
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
        #def precenceAvailable(event):
            #data = event.getStanzaValues()
            #print("Alguien se conceto")
            #print(data)
            #print(data['from'].jid)

        def nuevoAmigo(event):
            data = event.getStanzaValues()
            print("Nuevo amigo i hope so")
            print(data['from'])
            json1 = {"action":"FriendRequest","friend": str(data['from'])}
            json1 = json.dumps(json1)

            for c in cl:
                c.write_message(json1)

        def precenceUnavailable(event):
            data = event.getStanzaValues()
            print("No disponible")
            print(xmpp.boundjid.bare)
            print(str(((data['from'].jid).split('/'))[0]))
            if(str(((data['from'].jid).split('/'))[0]) != str(xmpp.boundjid.bare)):
                print(data)

                print(data['type'])
                print(str(((data['from'].jid).split('/'))[0]))
                data = {"action":"PresenceUpdate","value" : data['type'],"sender": str(((data['from'].jid).split('/'))[0])}
                jsonMessages.append(data)
                jsonPrecense.append(data)
                data = json.dumps(data)

                for c in cl:
                    c.write_message(data)

        def muc_message(event):
            pass

        def Roster(event):
            print("nuevo Amigo3")
            #msgLocations = {sleekxmpp.stanza.presence.Presence: "status",
            #      sleekxmpp.stanza.message.Message: "body"}

            data = event.getStanzaValues()

            del data['roster']['ver']
            print(data)

            for item in data['roster']['items']:
                json1 = {}
                print(str(item.jid))
                print(str(data['roster']['items'][item]['ask']))
                #data['roster']['items'][item] = str(data(item))
                #if(str(data['roster']['items'][item]['ask']) == "subscribe"):
                    #print("Friend Request")
                    #json1 = {"action":"FriendRequest","friend": str(item.jid)}
                #else:
                json1 = {"action":"Roster","friend": str(item.jid)}
                json1 = json.dumps(json1)
                for c in cl:
                    c.write_message(json1)

            resultat = []
            for i in res:
                resultat.append(i)
                #print(i)
                data = {"value" : i[0], "sender": i[1]}
                data = json.dumps(data)
                for c in cl:
                    c.write_message(data)
            for i in jsonPrecense:
                for c in cl:
                    c.write_message(i)

            #json.dumps(your_data, ensure_ascii=False)
            #data = {"value" : "Roster Conseguido"}
            #data = json.loads(json.dumps(data, ensure_ascii=False))
            #print(xmpp.roster)
            #for c in cl:
                #c.write_message(data)
        print(xmpp)
        xmpp.add_event_handler("session_start", start)
        xmpp.add_event_handler("failed_auth", failed)
        xmpp.add_event_handler("disconnected", disconnected)
        xmpp.add_event_handler("message",messageReceived)
        xmpp.add_event_handler("disconnected", disconnected)
        xmpp.add_event_handler("changed_subscription",nuevoAmigo)
        #xmpp.add_event_handler("presence_available",precenceAvailable)
        xmpp.add_event_handler("changed_status",precenceUnavailable)

        xmpp.add_event_handler("groupchat_message", muc_message)
        xmpp.send_presence()
        #xmpp.add_event_handler("presence_subscribed",subscribe)
        #xmpp.add_event_handler("roster_update",roster_update)

        # If you are working with an OpenFire server, you may need
        # to adjust the SSL version used:
        # xmpp.ssl_version = ssl.PROTOCOL_SSLv3
        # If you want to verify the SSL certificates offered by a server:
        xmpp.register_plugin('xep_0045')
        XMPP_CA_CERT_FILE = None
        #xmpp.ca_certs = None

        # Connect to the XMPP server and start processing XMPP stanzas.

        if xmpp.connect(reattempt=False,use_tls=False):
            # If you do not have the dnspython library installed, you will need
            # to manually specify the name of the server if it does not match
            # the one in the JID. For example, to use Google Talk you would
            # need to use:
            #
            # if xmpp.connect(('talk.google.com', 5222)):
            #     ...
            print("conecto")
            xmpp.process(block=False)
            xmpp.get_roster(callback= Roster)
            #print(xmpp.client_roster)

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
        def Roster(event):
            print("nuevo Amigo3")
            #msgLocations = {sleekxmpp.stanza.presence.Presence: "status",
            #      sleekxmpp.stanza.message.Message: "body"}

            data = event.getStanzaValues()

            del data['roster']['ver']
            print(data)
            json4 = {"action":"DeleteRoster"}
            json4 = json.dumps(json4)
            for c in cl:
                c.write_message(json4)
            for item in data['roster']['items']:
                json1 = {}
                print(str(item.jid))
                print(str(data['roster']['items'][item]['ask']))
                #data['roster']['items'][item] = str(data(item))
                #if(str(data['roster']['items'][item]['ask']) == "subscribe"):
                    #print("Friend Request")
                    #json1 = {"action":"FriendRequest","friend": str(item.jid)}
                #else:
                json1 = {"action":"Roster","friend": str(item.jid)}
                json1 = json.dumps(json1)
                for c in cl:
                    c.write_message(json1)

            resultat = []
            for i in res:
                resultat.append(i)
                #print(i)
                data = {"value" : i[0], "sender": i[1]}
                data = json.dumps(data)
                for c in cl:
                    c.write_message(data)
            for i in jsonPrecense:
                for c in cl:
                    c.write_message(i)
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
        if(action == "getImportant"):
            print("importantes")
            conn = sqlite3.connect('important.db')
            c = conn.cursor()
            c.execute('select * from messages')
            res = c.fetchall()

            for resu in res:
                print(resu[2])
                if(resu[2] == "1"):
                    json1 = {"action":resu[3],"value":resu[1],"sender":resu[0]}
                    json1 = json.dumps(json1)
                    for c in cl:
                        c.write_message(json1)
                else:
                    json1 = {"action":resu[3],"value":resu[1],"sender":resu[0],"status":1}
                    json1 = json.dumps(json1)
                    for c in cl:
                        c.write_message(json1)
        if(action == "saveImportant"):
            value = self.get_argument("value")
            valor = value.split(":")
            valor.append("newMessage")
            conn = sqlite3.connect('important.db')
            c = conn.cursor()
            print(sqlite3.paramstyle)
            c.execute("insert into messages values(? ,?, ?, ?)",valor)
            conn.commit()
            #c = conn.cursor()
            #c.execute('select * from messages')
            #res = c.fetchall()
            #c = conn.cursor()


        if(action =="send"):
            to = self.get_argument("to")
            message = self.get_argument("message")
            user = self.get_argument("ussername")

            mtype = self.get_argument("type");

            print(message)
            Clientes[0].send_message(mto=to, mbody=message,mtype=mtype)
            urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', message)
            if urls:
                message = "<a href='"+urls[0]+"'>"+urls[0]+"</a>"

            data = {"action":"newMessage","value":message, "sender": to,"status":"1"}
            data = json.dumps(data)
            jsonMessages.append(data)

            for c in cl:
                if(mtype != "groupchat"):
                    c.write_message(data)

            #Clientes.remove(Clientes[0])
        if(action =="getMessages"):
            #conn = sqlite3.connect('database.db')
            #c = conn.cursor()
            #c.execute('select * from messages')
            #res = c.fetchall()
            #resultat = []
            for i in jsonMessages :

                for c in cl:
                    c.write_message(i)
        if(action =="Request"):
            friend = self.get_argument("value")
            status = self.get_argument("status")
            Clientes[0].send_presence(pto = friend, ptype = status)
            Clientes[0].get_roster(callback = Roster)
        if(action == "Presence"):
            presencia = self.get_argument("value")
            Clientes[0].sendPresence(ptype = presencia)
        if(action== "AddFriend"):
            friend = self.get_argument("friend")
            Clientes[0].send_presence(pto=friend, ptype='subscribe')

            Clientes[0].get_roster(callback = Roster)
        if(action == "DeleteFriend"):
            print("Whaat really")
            friend = self.get_argument("friend")
            Clientes[0].update_roster(friend,subscription='remove')
            Clientes[0].get_roster(callback = Roster)

        if(action == "JoinGroup"):
            print("What the fuck man")
            room = self.get_argument("room")
            nick = self.get_argument("nick")
            Clientes[0].plugin['xep_0045'].joinMUC(room,nick,wait=True)
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
    #jsonMessages = []
    if(ioloop.IOLoop.initialized()):
        print(ioloop.IOLoop.instance())
    ioloop.IOLoop.instance().start()
