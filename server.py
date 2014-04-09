import tornado.ioloop
import tornado.web
import tornado.httpserver
from tornado.options import define, options
from tornado.escape import url_escape
from tornado.web import StaticFileHandler, RequestHandler, authenticated,asynchronous
from tornado.httpclient import AsyncHTTPClient
from tornado import gen
from os.path import abspath, dirname, join
import cobra.test
import json
from theseus import models
from jinja2 import Environment, FileSystemLoader
import psycopg2


define("port", default = 8888, help="run on the given port", type=int)

env = Environment(loader=FileSystemLoader('templates'))

directory = abspath(dirname(__file__))
#model = cobra.test.create_test_model()

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
                    (r"/", MainHandler),
                    (r"/models/(.*)/reactions/(.*)",ReactionDisplayHandler),
                    (r"/auth/login", AuthLoginHandler),
                    (r"/auth/logout", AuthLogoutHandler),
                    (r"/api/models/(.*)/genes",GeneListHandler),
                    (r"/api/models/(.*)/metabolites",MetaboliteListHandler),
                    (r"/api/models/(.*)/metabolites/(.*)",MetaboliteHandler),
                    (r"/api/models/(.*)/genes/(.*)",GeneHandler),
                    (r"/api/models/(.*)/reactions/(.*)", ReactionHandler),
                    (r"/api/models/(.*)/reactions", ReactionListHandler),
                    (r"/models/(.*)/reactions", ReactionListDisplayHandler),
                    (r"/api/models/(.*)", ModelHandler),
                    (r"/api/models",ModelListHandler),
                    (r"/models",ModelsListDisplayHandler),
                    (r"/search",SearchHandler),
                    (r"/about",AboutHandler),
                    (r"/assets/(.*)", StaticFileHandler,{'path':join(directory, 'assets')})
        ]
        
        settings = {
                    "login_url": "/auth/login",
                    "debug": "true",
                    "cookie_secret" : "asdflj12390jasdlfkjkjklasdf"
                    }
        tornado.web.Application.__init__(self, handlers, **settings)

class BaseHandler(RequestHandler):
    def get_current_user(self):
        user = self.get_secure_cookie("username")
        if (user):
            return user
        else:
            return None
class MainHandler(BaseHandler):
    def get(self):
        username = self.get_current_user()
        dictionary = {'user' : username}
        template = env.get_template("index.html")
        self.write(template.render(dictionary))
        self.set_header("Content-Type", "text/html")
        self.finish()

class AboutHandler(BaseHandler):
    def get(self):
        template = env.get_template("about.html")
        self.write(template.render())
        self.set_header("Content-Type", "text/html")
        self.finish()

class ReactionDisplayHandler(BaseHandler):
    @asynchronous
    @gen.engine
    def get(self, modelName, reactionName):
        template = env.get_template("reactions.html")
        http_client = AsyncHTTPClient()
        url_request = 'http://localhost:%d/api/models/%s/reactions/%s' % (options.port, modelName, reactionName)
        response = yield gen.Task(http_client.fetch, url_request)
        results = json.loads(response.body)
        metaboliteList = results['metabolites']
        id = results['id']
        name = results['name']
        dictionary = {'metaboliteList':metaboliteList,'name':name,'id':id, 'model':modelName}
        self.write(template.render(dictionary)) 
        self.finish() 


class ReactionHandler(BaseHandler):
    def get(self, modelName, reactionName):
            selectedModel = models.load_model(modelName)
            reactionDict = selectedModel.reactions
            reaction = reactionDict.get_by_id(reactionName)
            dictionary = {"id": reactionName, "name": reaction.name, "metabolites": [x.id for x in reaction._metabolites]}      
            data = json.dumps(dictionary)
            self.write(data)
            self.finish()
        
class ReactionListHandler(BaseHandler):
    def get(self, modelName):
        config = {}
        execfile("model_database/config", config) 
        conn_string = "host='%s' dbname='%s' user='%s' password='%s'"%(config['host'], config['dbname'], config['user'], config['password'])
        conn = psycopg2.connect(conn_string)
        cursor = conn.cursor()
        query = "select abbreviation, equation from reaction where reaction.modelversion_id = %s" %(modelName)
        cursor.execute(query)
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        data = json.dumps(results)    
        self.write(data)
        self.finish()

class ModelsListDisplayHandler(BaseHandler):
    @asynchronous
    @gen.engine
    def get(self):
        template = env.get_template("listdisplay.html")
        http_client = AsyncHTTPClient()
        url_request = 'http://localhost:%d/api/models' % (options.port)
        response = yield gen.Task(http_client.fetch, url_request)
        dictionary = {"modelResults":json.loads(response.body),"Models":"Models"}
        self.write(template.render(dictionary)) 
        self.finish()

class ReactionListDisplayHandler(BaseHandler):
    @asynchronous
    @gen.engine
    def get(self, modelName):
        template = env.get_template("listdisplay.html")
        http_client = AsyncHTTPClient()
        url_request = 'http://localhost:%d/api/models/%s/reactions' % (options.port, modelName)
        response = yield gen.Task(http_client.fetch, url_request)
        dictionary = {"reactionResults":json.loads(response.body),"Reactions":"Reactions"}
        self.write(template.render(dictionary)) 
        self.finish()
         
class ModelListHandler(BaseHandler):
    def get(self):
        config = {}
        execfile("model_database/config", config) 
        conn_string = "host='%s' dbname='%s' user='%s' password='%s'"%(config['host'], config['dbname'], config['user'], config['password'])
        conn = psycopg2.connect(conn_string)
        cursor = conn.cursor()
        query = "select name, description from model"
        cursor.execute(query)
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        data = json.dumps(results)    
        self.write(data)
        self.finish()

class ModelHandler(BaseHandler):
    def get(self, modelName):
        if modelName =="":
            self.write("specify a model")
            self.finish()
        else:
            modelobject = models.load_model(modelName)
            genelist = modelobject.genes
            reactionlist = modelobject.reactions
            metabolitelist = modelobject.metabolites
            dictionary = {"model":modelName,"reaction_count":len(reactionlist),"metabolite_count":len(metabolitelist),
                    "gene_count": len(genelist) }
            
            #dictionary = {"name":modelName,"reaction": modelName}
            data = json.dumps(dictionary)
            self.write(data)
            self.finish()
class GeneListHandler(BaseHandler):
    def get(self, modelName):
        config = {}
        execfile("model_database/config", config) 
        conn_string = "host='%s' dbname='%s' user='%s' password='%s'"%(config['host'], config['dbname'], config['user'], config['password'])
        conn = psycopg2.connect(conn_string)
        cursor = conn.cursor()
        query = "select name, description from model"
        cursor.execute(query)
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        data = json.dumps(results)    
        self.write(data)
        self.finish()
class GeneHandler(BaseHandler):
    def get(self,modelName,geneId):
        selectedModel =models.load_model(modelName)
        reactions = selectedModel.genes.get_by_id(geneId).get_reaction()
        dictionary = {"id": geneId, "reactions": [x.id for x in reactions]}
        data = json.dumps(dictionary)
        self.write(data)
        self.finish()
class MetaboliteListHandler(BaseHandler):
    def get(self, modelName):
        selectedModel = models.load_model(modelName)
        metaboliteList = [x.id for x in selectedModel.metabolites]
        data = json.dumps(metaboliteList)
        self.write(data)
        self.finish()
class MetaboliteHandler(BaseHandler):
    def get(self, modelName, metaboliteId):
        selectedModel = models.load_model(modelName)
        name = selectedModel.metabolites.get_by_id(metaboliteId).name
        formula = selectedModel.metabolites.get_by_id(metaboliteId).formula
        reactions = selectedModel.metabolites.get_by_id(metaboliteId).get_reaction()
        dictionary = {'name': name, 'id': metaboliteId, 'formula': formula.id, 'reactions':[x.id for x in reactions]}
        data = json.dumps(dictionary)
        self.write(data)
        self.finish()
        
class SearchHandler(BaseHandler):
    def get(self):
        template = env.get_template("listdisplay.html")
        q = self.get_argument("q","")
        self.write(template.render())
        self.finish()
class AuthLoginHandler(BaseHandler):
    def get(self):
        template = env.get_template("login.html")
        url = {'post_url': "http://localhost:%d/login" % (options.port)}
        self.write(template.render(url))
    
    def set_current_username(self, user):
        if user:
            self.set_secure_cookie("username", user)
            self.redirect(self.get_argument("next","/"))
    
    def post(self):
        username = self.get_argument("username", "")
        password = self.get_argument("password", "")
        if username=="justin" and password == "root":
            self.set_current_username(username) 
            self.redirect(self.get_argument("next", "/"))
        else:
            error_msg = u"?error=" + url_escape("Login incorrect")
            self.redirect(u"/auth/login" +  error_msg)
    
        
class AuthLogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie("username")
        self.redirect(self.get_argument("next", "/"))
        

def main():
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
        
        
if __name__ == "__main__":
    main()   