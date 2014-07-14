import tornado.ioloop
import tornado.web
import tornado.httpserver
from tornado.options import define, options
from tornado.escape import url_escape
from tornado.web import StaticFileHandler, RequestHandler, authenticated, asynchronous
from tornado.httpclient import AsyncHTTPClient
from tornado import gen
from os.path import abspath, dirname, join
import simplejson as json
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
#in list display, change so that the each result states what model it is from. in other list
#displays, state the model all the elements are from.
#For list display, use a dictionary where the n
class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
                    (r"/", MainHandler),
                    (r"/models/(.*)/reactions/(.*)$",ReactionDisplayHandler),
                    (r"/api/models/(.*)/reactions/(.*)$", ReactionHandler),
                    (r"/api/models/(.*)/reactions$", ReactionListHandler),
                    (r"/universal/reactions/(.*)$", UniversalReactionHandler),
                    (r"/api/models/(.*)/genes/(.*)$", GeneHandler),
                    (r"/api/models/(.*)/genes$", GeneListHandler),
                    (r"/models/(.*)/genes$", GeneListDisplayHandler),
                    (r"/models/(.*)/reactions$", ReactionListDisplayHandler),
                    (r"/api/models/(.*)/metabolites/(.*)$", MetaboliteHandler),
                    (r"/universal/metabolites/(.*)$", UniversalMetaboliteHandler),
                    (r"/models/(.*)/metabolites/(.*)$",MetaboliteDisplayHandler),
                    (r"/api/models/(.*)/metabolites$", MetaboliteListHandler),
                    (r"/models/(.*)/genes/(.*)$",GeneDisplayHandler),
                    (r"/models/(.*)/metabolites$",MetabolitesListDisplayHandler),
                    (r"/api/models/(.*)$", ModelHandler),
                    (r"/api/models$", ModelListHandler),
                    (r"/models$", ModelsListDisplayHandler),
                    (r"/models/(.*)$", ModelDisplayHandler),
                    (r"/about$",AboutHandler),
                    (r"/search$",SearchHandler),
                    (r"/autocomplete$",AutoCompleteHandler),
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
        altModelList = []
        modelquery = ReactionQuery().get_model(modelName, session)
        reaction = ReactionQuery().get_reaction(reactionName, session)
        modelreaction = ReactionQuery().get_model_reaction(reaction.id, modelquery.id, session).first()
        for rxn in session.query(Model_Reaction).filter(Model_Reaction.reaction_id == reaction.id).all():
            if rxn.model_id != modelquery.id:
                altModel = session.query(Model).filter(Model.id == rxn.model_id).first()
                altModelList.append(altModel.name)
        metabolitelist = ReactionQuery().get_metabolite_list(modelquery, reaction, session)          
        reaction_string = StringBuilder().build_reaction_string(metabolitelist, modelreaction)
        genelist = ReactionQuery().get_gene_list(reactionName, session)
        templist = modelreaction.gpr.replace("(","").replace(")","").split()
        genelist2 = [name for name in templist if name !="or" and name !="and"]
        sortedMetaboliteList = sorted(metabolitelist, key=lambda metabolite: metabolite[0])
        dictionary = {"model":modelquery.name, "id": reaction.name, "name": reaction.long_name, 
                        "metabolites": sortedMetaboliteList, "gene_reaction_rule": modelreaction.gpr, 
                        "genes": genelist2, "reaction_string": reaction_string, "altModelList": altModelList }      
        data = json.dumps(dictionary, use_decimal=True)
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
        finalReactionList = []
        for reaction in reactionList:
            finalReactionList.append([modelName, reaction])
        data = json.dumps(finalReactionList)
        self.write(data)
        self.set_header('Content-type','json')
        self.finish()   
        
class ReactionListDisplayHandler(BaseHandler):
    @asynchronous
    @gen.engine
    def get(self, modelName):
        template = env.get_template("listdisplay.html")
        http_client = AsyncHTTPClient()
        url_request = 'http://localhost:%d/api/models/%s/reactions' % (options.port, modelName)
        response = yield gen.Task(http_client.fetch, url_request)
        dictionary = {"reactionResults":json.loads(response.body),"Reactions":"Reactions","model":modelName}
        self.write(template.render(dictionary)) 
        self.set_header('Content-type','text/html')
        self.finish()

class UniversalReactionHandler(BaseHandler):
    def get(self, reactionName):
        session = Session()
        reaction = ReactionQuery().get_reaction(reactionName, session)
        dictionary = {}
        reactionList = []
        model_reactions = session.query(Model_Reaction).filter(Model_Reaction.reaction_id == reaction.id).all()
        for mr in model_reactions:
            model = session.query(Model).filter(Model.id == mr.model_id).first()
            reaction = session.query(Reaction).filter(Reaction.id == mr.reaction_id).first()
            reactionList.append([model.name, reaction.name])
        dictionary = {"reactions":reactionList, "biggid":reactionName, "name": reaction.long_name}
        data = json.dumps(dictionary)
        self.write(data)
        self.set_header('Content-type','json')
        self.finish()
        
class SearchHandler(BaseHandler):
    def get(self):
        session = Session()
        similarityBoundary = str(.4)
        template = env.get_template("listdisplay.html")
        input = self.get_argument("query")
        reactionlist = []
        metabolitelist = []
        modellist = []
        genelist = []
        
        reactionQuery = "SELECT id, name, similarity(name,'"+input+"') as sim FROM reaction WHERE name % '"+input +"' AND similarity(name,'"+input+"')>"+similarityBoundary+" ORDER BY sim DESC"
        result = session.execute(reactionQuery)
        for row in result:
            for reaction in session.query(Model_Reaction).filter(Model_Reaction.reaction_id == row['id']).all():   
                model = session.query(Model).filter(Model.id == reaction.model_id).first()
                reactionlist.append([model.name, row['name']])
        
        componentQuery = "SELECT id, identifier, similarity(identifier,'"+input+"') as sim FROM component WHERE identifier % '"+input +"' AND (similarity(identifier,'"+input+"')>"+similarityBoundary+") ORDER BY sim DESC"
        result = session.execute(componentQuery)
        
        for row in result:
            for cc in session.query(Compartmentalized_Component).filter(Compartmentalized_Component.component_id == row['id']).all():
                for mcc in session.query(Model_Compartmentalized_Component).filter(Model_Compartmentalized_Component.compartmentalized_component_id ==cc.id).all():
                    model = session.query(Model).filter(Model.id == mcc.model_id).first()
                    metabolitelist.append([model.name, row['identifier']]) 
        
        modelQuery = "SELECT id, name, similarity(name,'"+input+"') as sim FROM model WHERE name % '"+input +"' AND (similarity(name,'"+input+"')>"+similarityBoundary+") ORDER BY sim DESC"
        result = session.execute(modelQuery)   
        for row in result:
            modellist.append(row['name']) 
        
        geneQuery = "SELECT id, name, similarity(name,'"+input+"') as sim FROM gene WHERE name % '"+input +"' AND similarity(name,'"+input+"')>"+similarityBoundary+" ORDER BY sim DESC"
        result = session.execute(geneQuery)
        for row in result:
            model_gene = session.query(Model_Gene).filter(Model_Gene.gene_id == row['id']).first()
            model = session.query(Model).filter(Model.id == model_gene.model_id).first()
            genelist.append([model.name, row['name']])
        
        reactionData = json.dumps(reactionlist)
        metaboliteData = json.dumps(metabolitelist)
        modelData = json.dumps(modellist)
        geneData = json.dumps(genelist)
        dictionary = {"reactionResults":json.loads(reactionData), "Reactions":"Reactions",
                        "metaboliteResults":json.loads(metaboliteData),
                        "Metabolites":"Metabolites", 
                        "modelResults":json.loads(modelData),"Models":"Models",
                        "geneResults":json.loads(geneData), "Genes":"Genes" } 
        self.write(template.render(dictionary)) 
        self.set_header('Content-type','text/html')
        self.finish()

class AutoCompleteHandler(BaseHandler):
    def get(self):
        session = Session()
        similarityBoundary = str(.4)
        template = env.get_template("listdisplay.html")
        input = self.get_argument("query")
        reactionlist = []
        metabolitelist = []
        modellist = []
        genelist = []
        
        reactionQuery = "SELECT DISTINCT name, similarity(name,'"+input+"') as sim FROM reaction WHERE name % '"+input +"' AND similarity(name,'"+input+"')>"+similarityBoundary+" ORDER BY sim DESC"
        result = session.execute(reactionQuery)
        for row in result:
            reactionlist.append([row['name'],row['sim']])
        
        componentQuery = "SELECT identifier, similarity(identifier,'"+input+"') as sim FROM component WHERE identifier % '"+input +"' AND (similarity(identifier,'"+input+"')>"+similarityBoundary+") ORDER BY sim DESC "
        result = session.execute(componentQuery)       
        for row in result:
            metabolitelist.append([row['identifier'],row['sim']]) 
        
        modelQuery = "SELECT DISTINCT name, similarity(name,'"+input+"') as sim FROM model WHERE name % '"+input +"' AND (similarity(name,'"+input+"')>"+similarityBoundary+") ORDER BY sim DESC"
        result = session.execute(modelQuery)   
        for row in result:
            modellist.append([row['name'],row['sim']]) 
        
        geneQuery = "SELECT DISTINCT name, similarity(name,'"+input+"') as sim FROM gene WHERE name % '"+input +"' AND similarity(name,'"+input+"')>"+similarityBoundary+" ORDER BY sim DESC"
        result = session.execute(geneQuery)
        for row in result:
            genelist.append([row['name'],row['sim']])
        
        x = 0
        dictionary = {}
        joinedlist = reactionlist + metabolitelist + modellist + genelist
        sortedJoinedList = sorted(joinedlist, key=lambda query: query[1], reverse=True)
        for result in sortedJoinedList:
            dictionary[str(x)] = result[0]
            x+=1  
        self.write(json.dumps(dictionary))
        self.set_header('Content-type','json')
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
        template = env.get_template("listdisplay.html")
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
        altModelList = []
        for cc in session.query(Compartmentalized_Component).filter(Compartmentalized_Component.component_id == componentquery.id).all():
            for mcc in session.query(Model_Compartmentalized_Component).filter(Model_Compartmentalized_Component.compartmentalized_component_id == cc.id).all():
                if mcc.model_id != modelquery.id:
                    altModel = session.query(Model).filter(Model.id == mcc.model_id).first()
                    altModelList.append(altModel.name)
                    
        reactionlist = []
        for x in MetaboliteQuery().get_reactions(metaboliteId, session):
            for model_reaction in MetaboliteQuery().get_model_reaction(x, session):
                model = MetaboliteQuery().get_model(model_reaction, session)
                if model.name == modelquery.name:
                    reactionlist.append(x.name)
        sortedReactionList = sorted(reactionlist)
        dictionary = {'name': componentquery.name, 'id': metaboliteId, 'model': modelquery.name, 'formula': componentquery.formula,'reactions':sortedReactionList, "altModelList": altModelList}
        data = json.dumps(dictionary)
        self.write(data)
        self.set_header('Content-type','json')
        self.finish()
        
class UniversalMetaboliteHandler(BaseHandler):
    def get(self, metaboliteId):
        session = Session()
        componentquery = session.query(Component).filter(Component.identifier == metaboliteId).first()
        model_components = session.query(Model_Compartmentalized_Component).join(Compartmentalized_Component).filter(Compartmentalized_Component.component_id == componentquery.id).all()
        dictionary = {}
        metaboliteList = []
        for mc in model_components:
            model = session.query(Model).filter(Model.id == mc.model_id).first()
            metaboliteList.append([model.name, componentquery.identifier])
        dictionary = {'name':componentquery.name, 'biggid': componentquery.identifier, 
                    'formula': componentquery.formula, 'metaboliteList':metaboliteList}
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
        metaboliteList = MetaboliteQuery().get_metabolite_list(modelName, session)
        finalMetaboliteList = []
        for metabolite in metaboliteList:
            finalMetaboliteList.append([modelName, metabolite])
        data = json.dumps(finalMetaboliteList)
        self.write(data)
        self.set_header('Content-type','json')
        self.finish()
        
class MetabolitesListDisplayHandler(BaseHandler):
    @asynchronous
    @gen.engine
    def get(self, modelName):
        template = env.get_template("listdisplay.html")
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
        template = env.get_template("listdisplay.html")
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
        altModelList = []
        gene = session.query(Gene).filter(Gene.name==geneId).first()
        for gm in session.query(Model_Gene).filter(Model_Gene.gene_id == gene.id).all():
            model = session.query(Model).filter(Model.id == gm.model_id).first()
            if model.name != modelName:
                altModelList.append(model.name)
        for instance in GeneQuery().get_model_reaction(geneId, session):
            model = GeneQuery().get_model(instance, session)
            if model.name == modelName:
                list = []
                list.append(instance.name)
                list.append(instance.gpr)
                geneList = instance.gpr.replace("(","").replace(")","").split()
                list.append([name for name in geneList if name !="or" and name !="and"])
                reactionList.append(list)
                
        dictionary = {"id": geneId, "model":modelName, "reactions": reactionList, "altModelList": altModelList}
        data = json.dumps(dictionary)
        self.write(data)
        self.set_header('Content-type','json')
        self.finish()
        
class UniversalGeneHandler(BaseHandler):
    def get(self, geneId):
        session = Session()
        gene = session.query(Gene).filter(Gene.name == geneId).first()
        model_genes = session.query(Model_Gene).filter(Model_Gene.gene_id == gene.id).all()
        geneList = []
        dictionary = {}
        for mg in model_genes:
            model = session.query(Model).filter(Model.id == mg.model_id).first()
            geneList.append([model.name, gene.name])
        dictionary = {"biggid":gene.name, "genelist":geneList}
        data = json.dumps(dictionary)
        self.write(data)
        self.set_header('Content-type', 'json')
        self.finish()

class GeneListHandler(BaseHandler):
    def get(self, modelName):
        session = Session()
        geneList = GeneQuery().get_gene_list(modelName, session)
        finalGeneList = []
        for gene in geneList:
            finalGeneList.append([modelName, gene])
        data = json.dumps(finalGeneList)
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
