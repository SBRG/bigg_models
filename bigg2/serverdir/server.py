import tornado.ioloop
import tornado.web
import tornado.httpserver
from tornado.options import define, options
from tornado.escape import url_escape
from tornado.web import StaticFileHandler, RequestHandler, authenticated, asynchronous
from tornado.httpclient import AsyncHTTPClient
from tornado import gen
from os.path import abspath, dirname, join
import json
from model import Model, Component, Reaction, Compartment, Metabolite, Compartmentalized_Component, Model_Reaction, Reaction_Matrix, GPR_Matrix, Model_Compartmentalized_Component, Model_Gene, Gene
from jinja2 import Environment, FileSystemLoader
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from contextlib import contextmanager
from collections import Counter


define("port", default= 8886, help="run on given port", type=int)

env = Environment(loader=FileSystemLoader('templates'))

directory = abspath(dirname(__file__))

urlBasePath = "http://localhost:8888/"

Session = sessionmaker()

engine = create_engine("postgresql://jslu@localhost:5432/bigg2")

#change the list display to tables instead of one by one boxes

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
                    (r"/", MainHandler),
                    (r"/models/(.*)/reactions/(.*)",ReactionDisplayHandler),
                    (r"/api/models/(.*)/reactions/(.*)", ReactionHandler),
                    (r"/api/models/(.*)/reactions", ReactionListHandler),
                    (r"/api/models/(.*)/genes/(.*)", GeneHandler),
                    (r"/api/models/(.*)/genes", GeneListHandler),
                    (r"/models/(.*)/genes", GeneListDisplayHandler),
                    (r"/models/(.*)/reactions", ReactionListDisplayHandler),
                    (r"/api/models/(.*)/metabolites/(.*)", MetaboliteHandler),
                    (r"/models/(.*)/metabolites/(.*)",MetaboliteDisplayHandler),
                    (r"/api/models/(.*)/metabolites", MetaboliteListHandler),
                    (r"/models/(.*)/genes/(.*)",GeneDisplayHandler),
                    (r"/models/(.*)/metabolites",MetabolitesListDisplayHandler),
                    (r"/api/models/(.*)", ModelHandler),
                    (r"/api/models", ModelListHandler),
                    (r"/models", ModelsListDisplayHandler),
                    (r"/models/(.*)", ModelDisplayHandler),
                    (r"/about",AboutHandler),
                    (r"/advancesearch",FormHandler),
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
		template = env.get_template('index.html')
		self.write(template.render())
		self.set_header('Content-type','text/html')
		self.finish()
		
class AboutHandler(BaseHandler):
	def get(self):
		template = env.get_template('about.html')
		self.write(template.render())
		self.set_header('Content-type','text/html')
		self.finish()

class FormHandler(BaseHandler):
	def get(self):
		template = env.get_template('advancesearch.html')
		self.write(template.render())
		self.set_header('Content-type','text/html')
		self.finish()
"""
class ReactionDisplayHandler(BaseHandler):
    @asynchronous
    @gen.engine
    def get(self, modelName, reactionName):
        template = env.get_template("reactions.html")
        http_client = AsyncHTTPClient()
        url_request = 'http://localhost:%d/api/models/%s/reactions/%s' % (options.port, modelName, reactionName)
        response = yield gen.Task(http_client.fetch, url_request)
        results = json.loads(response.body)
        self.write(template.render(results)) 
        self.finish()
"""
class ReactionHandler(BaseHandler):
    def get(self, modelName, reactionName):
        session = Session()
        dictionary = {}
        modelreaction = session.query(Model_Reaction, Reaction).join(Reaction).filter(reactionName == Reaction.name).first()[0]
        modelquery = session.query(Model).filter(Model.name == modelName).first()
        reaction = 	session.query(Model_Reaction, Reaction).join(Reaction).filter(reactionName == Reaction.name).first()[1]
        metabolitelist = [(x[0].identifier, int(x[1].stoichiometry)) for x in session.query(Component,Reaction_Matrix).join(Compartmentalized_Component).join(Reaction_Matrix).filter(Reaction_Matrix.reaction_id == reaction.id).all()]
        """
        post_reaction_string = ""
        pre_reaction_string = ""
        preCounter = Counter()
        postCounter = Counter()
        for metabolite in metabolitelist:
            if float(metabolite[1]) < 0:
                preCounter[metabolite[0]] += 1
            else:
                postCounter[metabolite[0]] += 1
        for value in preCounter.keys():
            if(preCounter[value]>1):
                pre_reaction_string += str(preCounter[value]) + " " + value + " + "   
            else:
                pre_reaction_string += " " + value + " + "   
        for value in postCounter.keys():
            if(postCounter[value]>1):
                post_reaction_string += str(postCounter[value]) + " " + value + " + " 
            else:
                post_reaction_string += " " + value + " + "
                
        if modelreaction.lowerbound >= 0:
            reaction_string = pre_reaction_string[:-2] + " -> " + post_reaction_string[:-2]
        else:
            reaction_string = pre_reaction_string[:-2] + " <=> " + post_reaction_string[:-2]
        """
        post_reaction_string =""
        pre_reaction_string =""
        for metabolite in metabolitelist:
            if float(metabolite[1])<0:
                if float(metabolite[1])!= -1:
                    pre_reaction_string += str(abs(metabolite[1])) + " " + metabolite[0] + " + "
                else:
                    pre_reaction_string += " " + metabolite[0] + " + "
            if float(metabolite[1])>0:
                if float(metabolite[1])!= 1:
                    post_reaction_string += str(abs(metabolite[1])) + " " + metabolite[0] + " + "
                else:
                    post_reaction_string += " " + metabolite[0] + " + "
        if modelreaction.lowerbound >= 0:
            reaction_string = pre_reaction_string[:-2] + " -> " + post_reaction_string[:-2]
        else:
            reaction_string = pre_reaction_string[:-2] + " <=> " + post_reaction_string[:-2]
        
        genelist = [x.name for x in session.query(Gene).join(Model_Gene).join(GPR_Matrix).join(Model_Reaction).join(Reaction).filter(reactionName == Reaction.name).all()]
        templist = modelreaction.gpr.replace("(","").replace(")","").split()
        genelist2 = [name for name in templist if name !="or" and name !="and"]
        dictionary = {"model":modelquery.name, "id": reaction.name, "name": reaction.long_name, "metabolites": metabolitelist, "gene_reaction_rule": modelreaction.gpr, "genes": genelist2, "reaction_string": reaction_string }      
        data = json.dumps(dictionary)
        self.write(data)
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
        self.write(template.render(results)) 
        self.set_header('Content-type','text/html')
        self.finish() 

class ReactionListHandler(BaseHandler):
	def get(self, modelName):
		session = Session()
		reactionList = [x.name for x in session.query(Reaction).join(Model_Reaction).join(Model).filter(Model.name == modelName).all()]
		#selectedModel = models.load_model(modelName)		
		data = json.dumps(reactionList)
		self.write(data)
		self.finish()	
		
class ReactionListDisplayHandler(BaseHandler):
    @asynchronous
    @gen.engine
    def get(self, modelName):
        template = env.get_template("listdisplay2.html")
        http_client = AsyncHTTPClient()
        url_request = 'http://localhost:%d/api/models/%s/reactions' % (options.port, modelName)
        response = yield gen.Task(http_client.fetch, url_request)
        #selectedModel = models.load_model(modelName)
        #model = selectedModel.id.replace(" ","_")
        dictionary = {"reactionResults":json.loads(response.body),"Reactions":"Reactions","model":modelName}
        self.write(template.render(dictionary)) 
        self.set_header('Content-type','text/html')
        self.finish()	

class ModelHandler(BaseHandler):
    def get(self, modelName):
    	session = Session()
        if modelName =="":
            self.write("specify a model")
            self.finish()
        else:
            modelquery = session.query(Model).filter(Model.name == modelName).first()
            reactionquery = session.query(Model_Reaction).filter(Model_Reaction.model_id == modelquery.id).count()
            metabolitequery = session.query(Model_Compartmentalized_Component).filter(Model_Compartmentalized_Component.model_id == modelquery.id).count()
            genequery = session.query(Model_Gene).filter(Model_Gene.model_id == modelquery.id).count()
            dictionary = {"model":modelquery.name,"reaction_count":reactionquery,"metabolite_count":metabolitequery,
                   "gene_count": genequery }
            data = json.dumps(dictionary)
            self.write(data)
            self.finish()

class ModelDisplayHandler(BaseHandler):
	@asynchronous
	@gen.engine
	def get(self, modelName):
		template = env.get_template("model.html")
		http_client = AsyncHTTPClient()
		url_request = 'http://localhost:%d/api/models/%s' % (options.port, modelName)
		response = yield gen.Task(http_client.fetch, url_request)
		results = json.loads(response.body)
		self.write(template.render(results))
		self.set_header('Content-type','text/html')
		self.finish() 
            
class ModelListHandler(BaseHandler):
	def get(self):
		session = Session()
		uneditedlist = [x.name for x in session.query(Model).all()]
		
		#uneditedlist = models.get_model_list()

		data = json.dumps(uneditedlist)    
		self.write(data)
		self.finish()

class ModelsListDisplayHandler(BaseHandler):
    @asynchronous
    @gen.engine
    def get(self):
        template = env.get_template("listdisplay2.html")
        http_client = AsyncHTTPClient()
        url_request = 'http://localhost:%d/api/models' % (options.port)
        response = yield gen.Task(http_client.fetch, url_request)
        dictionary = {"modelResults":json.loads(response.body),"Models":"Models"}
        self.write(template.render(dictionary)) 
        self.set_header('Content-type','text/html')
        self.finish()
     

class MetaboliteHandler(BaseHandler):
    def get(self, modelName, metaboliteId):
        session = Session()
       	modelquery = session.query(Model).filter(Model.name == modelName).first()
       	componentquery = session.query(Component).filter(Component.identifier == metaboliteId).first()
        reactionlist = []
       	#reactionlist = [x.name for x in session.query(Reaction).join(Reaction_Matrix).join(Compartmentalized_Component).join(Component).filter(Component.identifier == metaboliteId).all()]
       	for x in session.query(Reaction).join(Reaction_Matrix).join(Compartmentalized_Component).join(Component).filter(Component.identifier == metaboliteId).all():
       	    modelReaction = session.query(Model_Reaction).join(Reaction).filter(Reaction.id == x.id).first()
       	    model = session.query(Model).filter( Model.id == modelReaction.model_id).first()
       	    if model.name == modelName:
       	        reactionlist.append(x.name)
       	dictionary = {'name': componentquery.name, 'id': metaboliteId, 'model': modelquery.name, 'formula': componentquery.formula,'reactions':reactionlist}
        data = json.dumps(dictionary)
        self.write(data)
        self.finish()
        
class MetaboliteDisplayHandler(BaseHandler):
	@asynchronous
	@gen.engine
	def get(self, modelName, metaboliteId):
		template = env.get_template("metabolites.html")
		http_client = AsyncHTTPClient()
		url_request = 'http://localhost:%d/api/models/%s/metabolites/%s' % (options.port, modelName, metaboliteId)
		response = yield gen.Task(http_client.fetch, url_request)
		results = json.loads(response.body)
		self.write(template.render(results))
		self.set_header('Content-type','text/html')
		self.finish()   

class MetaboliteListHandler(BaseHandler):
    def get(self, modelName):
    	session = Session()
    	metaboliteList = [x.identifier for x in session.query(Component).join(Compartmentalized_Component).join(Model_Compartmentalized_Component).join(Model).filter(Model.name == modelName).all()]
        #selectedModel = models.load_model(modelName)
        #metaboliteList = [x.id for x in selectedModel.metabolites]
        data = json.dumps(metaboliteList)
        self.write(data)
        self.finish()
        
class MetabolitesListDisplayHandler(BaseHandler):
    @asynchronous
    @gen.engine
    def get(self, modelName):
        template = env.get_template("listdisplay2.html")
        http_client = AsyncHTTPClient()
        url_request = 'http://localhost:%d/api/models/%s/metabolites' % (options.port, modelName)
        response = yield gen.Task(http_client.fetch, url_request)
        dictionary = {"metaboliteResults":json.loads(response.body),"Metabolites":"Metabolites", "model":modelName}
        self.write(template.render(dictionary)) 
        self.finish()
 
class GeneListDisplayHandler(BaseHandler):
    @asynchronous
    @gen.engine
    def get(self, modelName):
        template = env.get_template("listdisplay2.html")
        http_client = AsyncHTTPClient()
        url_request = 'http://localhost:%d/api/models/%s/genes' % (options.port, modelName)
        response = yield gen.Task(http_client.fetch, url_request)
        dictionary = {"geneResults":json.loads(response.body),"Genes":"Genes", "model":modelName}
        self.write(template.render(dictionary)) 
        self.finish()
 
class GeneHandler(BaseHandler):
    def get(self,modelName,geneId):
        session = Session()
        reactionList = []
        
        #reactionquery = session.query(Model_Reaction).join(Model).filter(Model.name == modelName).first()
        for instance in session.query(Model_Reaction).join(GPR_Matrix).join(Model_Gene).join(Gene).filter(Gene.name == geneId):
            model = session.query(Model).filter( Model.id == instance.model_id).first()
            if model.name == modelName:
                list = []
                list.append(instance.name)
                list.append(instance.gpr)
            
                geneList = instance.gpr.replace("(","").replace(")","").split()
            
                list.append([name for name in geneList if name !="or" and name !="and"])
                reactionList.append(list)
        dictionary = {"id": geneId, "model":modelName, "reactions": reactionList}
        data = json.dumps(dictionary)
        self.write(data)
        self.finish() 
class GeneListHandler(BaseHandler):
    def get(self, modelName):
    	session = Session()
    	geneList = [x.name for x in session.query(Gene).join(Model_Gene).join(Model).filter(Model.name == modelName).all()]
        #selectedModel = models.load_model(modelName)
        #metaboliteList = [x.id for x in selectedModel.metabolites]
        data = json.dumps(geneList)
        self.write(data)
        self.finish()
class GeneDisplayHandler(BaseHandler):
	@asynchronous
	@gen.engine
	def get(self, modelName, geneId):
		template = env.get_template("genes.html")
		http_client = AsyncHTTPClient()
		url_request = 'http://localhost:%d/api/models/%s/genes/%s' % (options.port, modelName, geneId)
		response = yield gen.Task(http_client.fetch, url_request)
		results = json.loads(response.body)
		self.write(template.render(results))
		self.finish() 
    
def main():
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
        
        
        
if __name__ == "__main__":
    main()   
