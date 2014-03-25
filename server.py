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



define("port", default = 8881, help="run on the given port", type=int)

env = Environment(loader=FileSystemLoader('templates'))

directory = abspath(dirname(__file__))
model = cobra.test.create_test_model()

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
                    (r"/", MainHandler),
                    (r"/auth/login", AuthLoginHandler),
                    (r"/auth/logout", AuthLogoutHandler),
                    (r"/api/models/(.*)/reactions/(.*)", ReactionHandler),
                    (r"/api/models/(.*)/reactions", ReactionListHandler),
                    (r"/api/models/(.*)", ModelHandler),
                    (r"/api/models",ModelListHandler),
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
    @authenticated
    def get(self):
        username = self.get_current_user()
        dictionary = {'user' : username}
        template = env.get_template("index.html")
        self.write(template.render(dictionary))
        self.set_header("Content-Type", "text/html")
        self.finish()

class ReactionHandler(BaseHandler):
    @authenticated
    def get(self, modelName, reactionName):
        if reactionName == "":
            self.write("specify a reaction id")
            self.finish()
        else:
            selectedModel = models.load_model(modelName)
            reactionDict = selectedModel.reactions
            reaction = reactionDict.get_by_id(reactionName)
            #reaction = selectedModel.reactions.get_by_id(reactionName)
            #dictionary = {"genes":,"reaction": reaction.reaction}
            #data = json.dumps(reactionDict.list_attr)
            dictionary = {"id": reactionName, "name": reaction.name, "metabolites": [x.id for x in reaction._metabolites]}
            
            data = json.dumps(dictionary)
            self.write(data)
            self.finish()
        
class ReactionListHandler(BaseHandler):
    @authenticated
    def get(self, modelName):
        selectedModel = models.load_model(modelName)
        #reactionDict = selectedModel.reactions
        data = json.dumps([x.id for x in selectedModel.reactions])
        self.write(data)
        self.finish()
        
class ModelListHandler(BaseHandler):
    @authenticated
    def get(self):
        modellist = models.get_model_list()
        #dictionary = {"name":reaction.name,"reaction": reaction.reaction}
        data = json.dumps(modellist)    
        self.write(data)
        self.finish()
        return data

class ModelHandler(BaseHandler):
    @authenticated
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