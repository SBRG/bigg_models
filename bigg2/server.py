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
from load.model import (Model, Component, Reaction,Compartment, Metabolite,
                        Compartmentalized_Component, Model_Reaction, Reaction_Matrix,
                        GPR_Matrix, Model_Compartmentalized_Component, Model_Gene, Gene)
from jinja2 import Environment, FileSystemLoader
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from contextlib import contextmanager
from collections import Counter
from load.queries import (ReactionQuery, ModelQuery, MetaboliteQuery,
                        GeneQuery, StringBuilder)


define("port", default= 8886, help="run on given port", type=int)

env = Environment(loader=FileSystemLoader('templates'))

directory = abspath(dirname(__file__))

urlBasePath = "http://localhost:8888/"

engine = create_engine("postgresql://dbuser@localhost:5432/bigg2")

Session = sessionmaker(bind = engine)

#make a tutorial on how to make a api request using curl
#http://www.restapitutorial.com/

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
                    (r"/", MainHandler),
                    (r"/models/(.*)/reactions/(.*)$",ReactionDisplayHandler),
                    (r"/api/models/(.*)/reactions/(.*)$", ReactionHandler),
                    (r"/api/models/(.*)/reactions$", ReactionListHandler),
                    (r"/api/models/(.*)/genes/(.*)$", GeneHandler),
                    (r"/api/models/(.*)/genes$", GeneListHandler),
                    (r"/models/(.*)/genes$", GeneListDisplayHandler),
                    (r"/models/(.*)/reactions$", ReactionListDisplayHandler),
                    (r"/api/models/(.*)/metabolites/(.*)$", MetaboliteHandler),
                    (r"/models/(.*)/metabolites/(.*)$",MetaboliteDisplayHandler),
                    (r"/api/models/(.*)/metabolites$", MetaboliteListHandler),
                    (r"/models/(.*)/genes/(.*)$",GeneDisplayHandler),
                    (r"/models/(.*)/metabolites$",MetabolitesListDisplayHandler),
                    (r"/api/models/(.*)$", ModelHandler),
                    (r"/api/models$", ModelListHandler),
                    (r"/models$", ModelsListDisplayHandler),
                    (r"/models/(.*)$", ModelDisplayHandler),
                    (r"/about$",AboutHandler),
                    (r"/listdisplay$",ListDisplayHandler),
                    (r"/advancesearch$",FormHandler),
                    (r"/static/(.*)$", StaticFileHandler,{'path':join(directory, 'static')})
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
		
class ReactionHandler(BaseHandler):
    def get(self, modelName, reactionName):
        session = Session()
        dictionary = {}
        modelreaction = ReactionQuery().get_model_reaction(reactionName, session)
        modelquery = ReactionQuery().get_model(modelName, session)
        reaction = ReactionQuery().get_reaction(reactionName, session)
        metabolitelist = ReactionQuery().get_metabolite_list(reaction, session)
        reaction_string = StringBuilder().build_reaction_string(metabolitelist, modelreaction)
        genelist = ReactionQuery().get_gene_list(reactionName, session)
        templist = modelreaction.gpr.replace("(","").replace(")","").split()
        genelist2 = [name for name in templist if name !="or" and name !="and"]
        dictionary = {"model":modelquery.name, "id": reaction.name, "name": reaction.long_name, 
		                "metabolites": metabolitelist, "gene_reaction_rule": modelreaction.gpr, 
		                "genes": genelist2, "reaction_string": reaction_string }	  
        data = json.dumps(dictionary)
        self.write(data)
        self.set_header('Content-type','json')
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
        reactionList = ReactionQuery().get_reaction_list(modelName, session)	
        data = json.dumps(reactionList)
        self.write(data)
        self.set_header('Content-type','json')
        self.finish()	
		
class ReactionListDisplayHandler(BaseHandler):
    @asynchronous
    @gen.engine
    def get(self, modelName):
        template = env.get_template("listdisplay2.html")
        http_client = AsyncHTTPClient()
        url_request = 'http://localhost:%d/api/models/%s/reactions' % (options.port, modelName)
        response = yield gen.Task(http_client.fetch, url_request)
        dictionary = {"reactionResults":json.loads(response.body),"Reactions":"Reactions","model":modelName}
        self.write(template.render(dictionary)) 
        self.set_header('Content-type','text/html')
        self.finish()
        
class ListDisplayHandler(BaseHandler):

    def get(self):
        session = Session()
        template = env.get_template("listdisplay2.html")
        input = self.get_argument("input")
        reactionlist = []
        query = "SELECT name FROM reaction WHERE name % '"+input +"' AND similarity(name,'"+input+"')>.5"
        result = session.execute(query)
        for row in result:
             reactionlist.append(row['name'])
        data = json.dumps(reactionlist)
        dictionary = {"reactionResults":json.loads(data), "Reactions":"Reactions","model":"iJO1366"} 
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
            modelquery = ModelQuery().get_model(modelName, session)
            reactionquery = ModelQuery().get_model_reaction_count(modelquery, session)
            metabolitequery = ModelQuery().get_model_metabolite_count(modelquery, session)
            genequery = ModelQuery().get_gene_count(modelquery, session)
            dictionary = {"model":modelquery.name,"reaction_count":reactionquery,"metabolite_count":metabolitequery,
				   "gene_count": genequery }
            data = json.dumps(dictionary)
            self.write(data)
            self.set_header('Content-type','json')
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
        modellist = ModelQuery().get_model_list(session)
        data = json.dumps(modellist)	   
        self.write(data)
        self.set_header('Content-type','json')
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
		self.set_header('Content-type','text/html')
		self.finish()
	 

class MetaboliteHandler(BaseHandler):
    def get(self, modelName, metaboliteId):
        session = Session()
        modelquery = session.query(Model).filter(Model.name == modelName).first()
        componentquery = session.query(Component).filter(Component.identifier == metaboliteId).first()
        reactionlist = []
	    #for x in session.query(Reaction).join(Reaction_Matrix).join(Compartmentalized_Component).join(Component).filter(Component.identifier == metaboliteId).all():
        for x in MetaboliteQuery().get_reactions(metaboliteId, session):
		    #modelReaction = session.query(Model_Reaction).join(Reaction).filter(Reaction.id == x.id).first()
		    modelReaction = MetaboliteQuery().get_model_reaction(x, session)
		    #model = session.query(Model).filter( Model.id == modelReaction.model_id).first()
		    model = MetaboliteQuery().get_model(modelReaction, session)
		    if model.name == modelName:
			    reactionlist.append(x.name)
        dictionary = {'name': componentquery.name, 'id': metaboliteId, 'model': modelquery.name, 'formula': componentquery.formula,'reactions':reactionlist}
        data = json.dumps(dictionary)
        self.write(data)
        self.set_header('Content-type','json')
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
		#metaboliteList = [x.identifier for x in session.query(Component).join(Compartmentalized_Component).join(Model_Compartmentalized_Component).join(Model).filter(Model.name == modelName).all()]
		metaboliteList = MetaboliteQuery().get_metabolite_list(modelName, session)
		data = json.dumps(metaboliteList)
		self.write(data)
		self.set_header('Content-type','json')
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
        self.set_header('Content-type','text/html')
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
		self.set_header('Content-type','text/html') 
		self.finish()
 
class GeneHandler(BaseHandler):
	def get(self,modelName,geneId):
		session = Session()
		reactionList = []
		
		#reactionquery = session.query(Model_Reaction).join(Model).filter(Model.name == modelName).first()
		#for instance in session.query(Model_Reaction).join(GPR_Matrix).join(Model_Gene).join(Gene).filter(Gene.name == geneId):
		for instance in GeneQuery().get_model_reaction(geneId, session):
			#model = session.query(Model).filter( Model.id == instance.model_id).first()
			model = GeneQuery().get_model(instance, session)
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
		self.set_header('Content-type','json')
		self.finish()

class GeneListHandler(BaseHandler):
    def get(self, modelName):
        session = Session()
		#geneList = [x.name for x in session.query(Gene).join(Model_Gene).join(Model).filter(Model.name == modelName).all()]
        geneList = GeneQuery().get_gene_list(modelName, session)
        data = json.dumps(geneList)
        self.write(data)
        self.set_header('Content-type','json')
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
		self.set_header('Content-type','text/html')
		self.finish() 
	
def main():
	tornado.options.parse_command_line()
	http_server = tornado.httpserver.HTTPServer(Application())
	http_server.listen(options.port)
	tornado.ioloop.IOLoop.instance().start()
		
if __name__ == "__main__":
	main()	 
