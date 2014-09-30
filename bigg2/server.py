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
                        GPR_Matrix, Model_Compartmentalized_Component, Model_Gene, Gene, Comments, GenomeRegion, Genome)
from jinja2 import Environment, FileSystemLoader
from sqlalchemy.orm import sessionmaker, aliased
from sqlalchemy import create_engine, desc, func, or_
from contextlib import contextmanager
from collections import Counter
from load.queries import (ReactionQuery, ModelQuery, MetaboliteQuery,
                        GeneQuery, StringBuilder)

from download.sbml import sbmlio
#write_cobra_model_to_sbml_file(cobra_model, sbml_filename)

define("port", default= 8886, help="run on given port", type=int)

env = Environment(loader=FileSystemLoader('templates'))

directory = abspath(dirname(__file__))

urlBasePath = "http://localhost:8886/"

engine = create_engine("postgresql://dbuser@localhost:5432/ome")

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
                    (r"/api/universal/metabolites/(.*)$", UniversalMetaboliteHandler),
                    (r"/universal/metabolites/(.*)$", UniversalMetaboliteDisplayHandler),
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
                    (r"/search$",SearchDisplayHandler),
                    (r"/api/search$",SearchHandler),
                    (r"/autocomplete$",AutoCompleteHandler),
                    (r"/advancesearch$",FormHandler),
                    (r"/advancesearchresults$",FormResultsHandler),
                    (r"/sbml$",DownloadPageHandler),
                    (r"/webapi$",WebApiHandler),
                    (r"/submiterror$", SubmitErrorHandler),
                    (r"/download/(.*)$",DownLoadHandler,{'path':join(directory, 'download')}),
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
class DownLoadHandler(tornado.web.StaticFileHandler):
    def post(self, path, include_body=True):
        # your code from above, or anything else custom you want to do
        self.set_header('Content-Type','text/xml')  
        self.set_header('Accept-Ranges', 'bytes')  
        self.set_header('Content-Encoding', 'none')  
        self.set_header('Content-Disposition','attachment')
        super(StaticFileHandler, self).get(path, include_body) 
     
class SubmitErrorHandler(BaseHandler):
    def post(self):
        session = Session()
        email = self.get_argument("email", "empty")
        keggid = self.get_argument("keggid", "empty")
        casnumber = self.get_argument("casnumber", "empty")
        name = self.get_argument("name", "empty")
        formula = self.get_argument("formula", "empty")
        comments = self.get_argument("comments", "empty")
        message = Comments(kegg_id =keggid, cas_number=casnumber, name = name, formula = formula, text = comments)
        session.add(message)
        session.commit()
        session.close()
        self.write("message sent and saved")
        
class DownloadPageHandler(BaseHandler):
    def get(self):
        template = env.get_template('download.html')
        input = self.get_argument("query")
        model = sbmlio.createSBML(input)
        dictionary = {"xml":model.id + ".xml"}
        self.write(template.render(dictionary))
        self.set_header('Content-type','text/html')
        self.finish()
  
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
        
class WebApiHandler(BaseHandler):
    def get(self):
        template = env.get_template('webapi.html')
        self.write(template.render())
        self.set_header('Content-type','text/html')
        self.finish()

class FormHandler(BaseHandler):
    def get(self):
        template = env.get_template('advancesearch.html')
        session = Session()
        modellist = ModelQuery().get_model_list(session)
        dictionary = {"modelResults":modellist}
        self.write(template.render(dictionary))
        self.set_header('Content-type','text/html') 
        self.finish()
        session.close()
    
        #message = Comments(kegg_id =keggid, cas_number=casnumber, biggid = biggid, formula = formula, text = comments)
        #session.add(message)
        #session.commit()
        #session.close()
        #self.write(modelradios)
class FormResultsHandler(BaseHandler):
    def post(self):
        template = env.get_template("listdisplay.html")
        session = Session()
        allradio = self.get_argument("all", "empty")
        input = self.get_argument("query", "empty")
        modellist = []
        for m in session.query(Model).all():
            modellist.append([m.biggid , self.get_argument(m.biggid, "empty")])
        metaboliteradio = self.get_argument("metabolites", "empty")
        reactionradio = self.get_argument("reactions", "empty")
        generadio = self.get_argument("genes", "empty")
        genelist =[]
        reactions=[]
        metabolites=[]
        sqlstring = "select * from model"
        #model = session.query(Model).filter(Model.biggid.in_(modelradios.split(','))).all()
        metaboliteResults = []
        reactionResults = []
        geneResults = []
        modelResults = []
        similarityBoundary = str(.3)
        result = session.query(Metabolite.id, Metabolite.name, func.similarity(Metabolite.name, str(input)).label("sim")).filter(Metabolite.name % str(input)).filter(func.similarity(Metabolite.name, str(input))> similarityBoundary).order_by(desc('sim')).all()
      
        if metaboliteradio != "empty" or allradio !="empty":
            for modelName in modellist:
                model = session.query(Model).filter(Model.biggid == modelName[0]).first()
                if modelName[1] != "empty":
                    for row in result:
                        for cc in session.query(Compartmentalized_Component).filter(Compartmentalized_Component.component_id == row.id).distinct(Compartmentalized_Component.component_id).all():
                            for mcc in session.query(Model_Compartmentalized_Component).filter(Model_Compartmentalized_Component.compartmentalized_component_id ==cc.id).filter(Model_Compartmentalized_Component.model_id == model.id).all():
                                compartment = session.query(Compartment).join(Compartmentalized_Component).filter(Compartmentalized_Component.id == cc.id).first()
                                metaboliteResults.append([model.biggid, row.name + "_"+compartment.name]) 
                    """
                    metaboliteList = MetaboliteQuery().get_metabolite_list(modelName[0], session)
                    for metab in metaboliteList:
                        metaboliteResults.append([modelName[0], metab[0] + "_"+metab[1]])"""
        if reactionradio != "empty" or allradio !="empty":
            for modelName in modellist:
                if modelName[1] != "empty":
                    reactionList = ReactionQuery().get_reaction_list(modelName[0], session)
                    for r in reactionList:
                        reactionResults.append([modelName[0], r])
        if generadio != "empty" or allradio !="empty":
            for modelName in modellist:
                if modelName[1] != "empty":
                    geneList = GeneQuery().get_gene_list(modelName[0], session)
                    for g in geneList:
                        geneResults.append([modelName[0], g])               
                        
        
        
        dictionary = {"reactionResults":reactionResults, "Reactions":"Reactions",
                        "metaboliteResults":metaboliteResults,
                        "Metabolites":"Metabolites", 
                        "modelResults":modelResults,"Models":"Models",
                        "geneResults":geneResults, "Genes":"Genes" }
        #self.write()
        #self.set_header('Content-type','json')
        #json.dumps(dictionary)
        self.write(template.render(dictionary)) 
        self.set_header('Content-type','text/html')
        self.finish() 
        session.close()  
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
                altModelList.append(altModel.biggid)
        metabolitelist = ReactionQuery().get_metabolite_list(modelquery, reaction, session) 
        reaction_string = StringBuilder().build_reaction_string(metabolitelist, modelreaction)
        genelist = ReactionQuery().get_gene_list(reaction, modelquery, session)
        templist = modelreaction.gpr.replace("(","").replace(")","").split()
        genelist2 = [name for name in templist if name !="or" and name !="and"]
        sortedMetaboliteList = sorted(metabolitelist, key=lambda metabolite: metabolite[0])
        dictionary = {"model":modelquery.biggid, "name": reaction.name, "long_name": reaction.long_name, 
                        "metabolites": metabolitelist, "gene_reaction_rule": modelreaction.gpr, 
                        "genes": genelist, "reaction_string": reaction_string, "altModelList": altModelList}      
        data = json.dumps(dictionary, use_decimal=True)
        self.write(data)
        #self.write(json.dumps(metabolitelist))
        self.set_header('Content-type','json')
        self.finish()
        session.close()
        
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
        data = json.dumps(sorted(reactionList, key=lambda s: s.lower()))
        self.write(data)
        self.set_header('Content-type','json')
        self.finish()   
        session.close()
        
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
            reactionList.append([model.biggid, reaction.name])
        dictionary = {"reactions":reactionList, "biggid":reactionName, "name": reaction.name}
        data = json.dumps(dictionary)
        self.write(data)
        self.set_header('Content-type','json')
        self.finish()
        session.close()
        
class SearchHandler(BaseHandler):
    def get(self):
        session = Session()
        similarityBoundary = str(.3)
        template = env.get_template("listdisplay.html")
        input = self.get_argument("query")
        reactionlist = []
        metabolitelist = []
        modellist = []
        genelist = []
        
        result = session.query(Reaction.id, Reaction.name, func.similarity(Reaction.name, str(input)).label("sim")).filter(Reaction.name % str(input)).filter(func.similarity(Reaction.name, str(input))> similarityBoundary).order_by(desc('sim')).all()
        for row in result:
            for reaction in session.query(Model_Reaction).filter(Model_Reaction.reaction_id == row.id).all():   
                model = session.query(Model).filter(Model.id == reaction.model_id).first()
                reactionlist.append([model.biggid, row.name])
        
        result = session.query(Metabolite.id, Metabolite.name, func.similarity(Metabolite.name, str(input)).label("sim")).filter(Metabolite.name % str(input)).filter(func.similarity(Metabolite.name, str(input))> similarityBoundary).order_by(desc('sim')).all()
        for row in result:
            for cc in session.query(Compartmentalized_Component).filter(Compartmentalized_Component.component_id == row.id).distinct(Compartmentalized_Component.component_id).all():
                for mcc in session.query(Model_Compartmentalized_Component).filter(Model_Compartmentalized_Component.compartmentalized_component_id ==cc.id).all():
                    
                    model = session.query(Model).filter(Model.id == mcc.model_id).first()
                    compartment = session.query(Compartment).join(Compartmentalized_Component).filter(Compartmentalized_Component.id == cc.id).first()
                    metabolitelist.append([model.biggid, row.name + "_"+compartment.name]) 
           
        result = session.query(Model.id, Model.biggid, func.similarity(Model.biggid, str(input)).label("sim")).filter(Model.biggid % str(input)).filter(func.similarity(Model.biggid, str(input))> similarityBoundary).order_by(desc('sim')).all()
        for row in result:
            templist = []
            modelquery = ModelQuery().get_model(row.biggid, session)
            reactionquery = ModelQuery().get_model_reaction_count(modelquery, session)
            metabolitequery = ModelQuery().get_model_metabolite_count(modelquery, session)
            genequery = ModelQuery().get_gene_count(modelquery, session)
            genomequery = session.query(Genome).filter(Genome.id == modelquery.genome_id).first()
            templist.extend([row.biggid, genomequery.organism, metabolitequery, reactionquery, genequery]) 
            modellist.append(templist)
        result = session.query(Gene.id, Gene.name, func.similarity(Gene.name, str(input)).label("sim")).filter(Gene.name % str(input)).filter(func.similarity(Gene.name, str(input))> similarityBoundary).order_by(desc('sim')).all()
        for row in result:
            model_gene = session.query(Model_Gene).filter(Model_Gene.gene_id == row.id).first()
            if model_gene != None:
                model = session.query(Model).filter(Model.id == model_gene.model_id).first()
                genelist.append([model.biggid, row.name])
        session.close()
        dictionary = {"reactionResults":reactionlist, "Reactions":"Reactions",
                        "metaboliteResults":metabolitelist,
                        "Metabolites":"Metabolites", 
                        "modelResults":modellist,"Models":"Models",
                        "geneResults":genelist, "Genes":"Genes" } 
        self.write(json.dumps(dictionary)) 
        self.set_header('Content-type','json')
        self.finish()
        session.close()

class SearchDisplayHandler(BaseHandler):
    @asynchronous
    @gen.engine
    def get(self):
        template = env.get_template("listdisplay.html")
        http_client = AsyncHTTPClient()
        url_request = 'http://localhost:%d/api/search?query=%s' % (options.port, self.get_argument("query"))
        response = yield gen.Task(http_client.fetch, url_request)
        results = json.loads(response.body)
        self.write(template.render(results))
        self.set_header('Content-type','text/html')
        self.finish() 
    
class AutoCompleteHandler(BaseHandler):
    def get(self):
        session = Session()
        similarityBoundary = str(.2)
        template = env.get_template("listdisplay2.html")
        input = self.get_argument("query")
        reactionlist = []
        metabolitelist = []
        modellist = []
        genelist = []
        
        result = session.query(Reaction.id, Reaction.name, func.similarity(Reaction.name, str(input)).label("sim")).filter(Reaction.name % str(input)).filter(func.similarity(Reaction.name, str(input))> similarityBoundary).order_by(desc('sim')).all()
        for row in result:
            reactionlist.append([row.name,row.sim])
               
        result = session.query(Metabolite.id, Metabolite.name, func.similarity(Metabolite.name, str(input)).label("sim")).filter(Metabolite.name % str(input)).filter(func.similarity(Metabolite.name, str(input))> similarityBoundary).order_by(desc('sim')).all()
        for row in result:
            metabolitelist.append([row.name,row.sim]) 
        
        result = session.query(Model.id, Model.biggid, func.similarity(Model.biggid, str(input)).label("sim")).filter(Model.biggid % str(input)).filter(func.similarity(Model.biggid, str(input))> similarityBoundary).order_by(desc('sim')).all()   
        for row in result:
            modellist.append([row.biggid,row.sim]) 
        #distinctGene =aliased(Gene, func.distinct(Gene.name))
        result = session.query(Gene.name, func.similarity(Gene.name, str(input)).label("sim")).join(Model_Gene).filter(Gene.name % str(input)).filter(func.similarity(Gene.name, str(input))> similarityBoundary).order_by(desc('sim')).group_by(Gene.name).all()
        for row in result:
            gene = session.query(Gene).filter(Gene.name == row[0]).first()
            model_gene = session.query(Model_Gene).filter(Model_Gene.gene_id == gene.id).first()
            if model_gene != None:
                genelist.append([row[0],row[1]])  
        session.close()
        
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
        session.close()       

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
            genomequery = session.query(Genome).filter(Genome.id == modelquery.genome_id).first()
            dictionary = {"model":modelquery.biggid,"reaction_count":reactionquery,"metabolite_count":metabolitequery,
                   "gene_count": genequery, 'organism':genomequery.organism}
            data = json.dumps(dictionary)
            self.write(data)
            self.set_header('Content-type','json')
            self.finish()
            session.close()

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
        models = ModelQuery().get_model_list(session)
        modellist = []
        for model in models:
            templist = []
            modelquery = ModelQuery().get_model(model, session)
            reactionquery = ModelQuery().get_model_reaction_count(modelquery, session)
            metabolitequery = ModelQuery().get_model_metabolite_count(modelquery, session)
            genequery = ModelQuery().get_gene_count(modelquery, session)
            genomequery = session.query(Genome).filter(Genome.id == modelquery.genome_id).first()
            templist.extend([modelquery.biggid, genomequery.organism, metabolitequery, reactionquery,  genequery])
            modellist.append(templist)
        data = json.dumps(sorted(modellist, key=lambda s: s[0].lower()))
        self.write(data)
        self.set_header('Content-type','json')
        self.finish()
        session.close()

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
        
        modelquery = session.query(Model).filter(Model.biggid == modelName).first()
        componentquery = session.query(Metabolite).filter(Metabolite.name == metaboliteId.split("_")[0]).first()
        compartmentquery = session.query(Compartment).filter(Compartment.name == metaboliteId[-1:len(metaboliteId)]).first()
        metabolitequery = session.query(Metabolite).filter(componentquery.id == Metabolite.id).first()
        compartmentlist = []
        altModelList = []
        for cc in session.query(Compartmentalized_Component).filter(Compartmentalized_Component.component_id == componentquery.id).filter(Compartmentalized_Component.compartment_id == compartmentquery.id).all():         
            for mcc in session.query(Model_Compartmentalized_Component).filter(Model_Compartmentalized_Component.compartmentalized_component_id == cc.id).all():
                if mcc.model_id != modelquery.id:
                    altModel = session.query(Model).filter(Model.id == mcc.model_id).first()
                    altModelList.append(str(altModel.biggid))
                    
        reactionlist = []
        
        for x in MetaboliteQuery().get_model_reactions(componentquery.name, compartmentquery.name, modelquery, session):
            reactionlist.append(str(x.name))
               
        sortedReactionList = sorted(reactionlist)
        dictionary = {'name': str(componentquery.long_name), 'id': metaboliteId, 'universalname':componentquery.name, 'cas_number':str(metabolitequery.cas_number), 'kegg_id': str(metabolitequery.kegg_id),'reactions':reactionlist, 'model': str(modelquery.biggid), 'formula': str(metabolitequery.formula), "altModelList": altModelList}
        data = json.dumps(dictionary)
        
        self.write(data)
        self.set_header('Content-type','json')
        self.finish()
        session.close()
        
class UniversalMetaboliteHandler(BaseHandler):
    def get(self, metaboliteId):
        session = Session()
        componentquery = session.query(Metabolite).filter(Metabolite.name == metaboliteId).first()
        compartmentList = ['c', 'e', 'p']
        
        metaboliteList = []
        for c in compartmentList:
            temp_metaboliteList = []
            model_components = session.query(Model_Compartmentalized_Component).join(Compartmentalized_Component).join(Compartment).filter(Compartmentalized_Component.compartment_id == Compartment.id).filter(Compartmentalized_Component.component_id == componentquery.id).filter(Compartment.name == c).all()
            for mc in model_components:
                model = session.query(Model).filter(Model.id == mc.model_id).first()
                compartment = session.query(Compartment).filter(Compartment.id == mc.compartment_id).first()
                temp_metaboliteList.append([model.biggid, componentquery.name, compartment.name])
            metaboliteList.append(temp_metaboliteList)
        reactionList = []
        for c in compartmentList:
            temp_reactionList = [(x[0].name, x[1].biggid) for x in (session
                .query(Reaction, Model)
                .join(Model_Reaction)
                .join(Model)
                .join(Reaction_Matrix)
                .join(Compartmentalized_Component)
                .join(Compartment)
                .join(Component)
                .join(Metabolite)
                .filter(Compartment.name == c)
                .filter(Metabolite.name == metaboliteId)
                .all())]
            reactionList.append([c, temp_reactionList])
        
        dictionary = {'long_name':str(componentquery.long_name), 'name': str(componentquery.name), 'kegg_id': str(componentquery.kegg_id), 'cas_number':str(componentquery.cas_number), 
                    'formula': str(componentquery.formula), 'metaboliteList':metaboliteList, 'reactionList': reactionList}
        #dictionary = {}
        data = json.dumps(dictionary)
        self.write(data)
        self.set_header('Content-type','json')
        self.finish()
        session.close()            

class UniversalMetaboliteDisplayHandler(BaseHandler):
    @asynchronous
    @gen.engine
    def get(self, metaboliteId):
        template = env.get_template("universalmetabolites.html")
        http_client = AsyncHTTPClient()
        url_request = 'http://localhost:%d/api/universal/metabolites/%s' % (options.port, metaboliteId)
        response = yield gen.Task(http_client.fetch, url_request)
        results = json.loads(response.body)
        self.write(template.render(results))
        self.set_header('Content-type','text/html')
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
        session.close()
        
        data = json.dumps(sorted(metaboliteList, key=lambda metabolite: metabolite[0].lower()))
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
    def get(self,modelName,geneName):
        session = Session()
        reactionList = []
        altModelList = []
        gene = session.query(GenomeRegion).filter(GenomeRegion.name==geneName).first()
        #gene = session.query(Gene).filter(Gene.id == geneRegion.id).first()
        for gm in session.query(Model_Gene).filter(Model_Gene.gene_id == gene.id).all():
            model = session.query(Model).filter(Model.id == gm.model_id).first()
            if model.biggid != modelName:
                altModelList.append(model.biggid)
        for instance in GeneQuery().get_model_reaction(geneName, session):
            model = GeneQuery().get_model(instance, session)
            geneList = []
            if model.biggid == modelName:
                list = []
                list.append(instance.name)
                list.append(instance.gpr)
                for x in session.query(Gene).join(Model_Gene).join(GPR_Matrix).filter(GPR_Matrix.model_reaction_id == instance.id):
                    geneList.append([x.name,x.locus_id])
                list.append(geneList)
                #geneList = instance.gpr.replace("(","").replace(")","").split()
                #list.append([name for name in geneList if name !="or" and name !="and"])
                reactionList.append(list)       
        dictionary = {"name": geneName,"id":gene.locus_id, "model":modelName, "reactions": reactionList, "altModelList": altModelList, "info":gene.info, "leftpos":gene.leftpos,"rightpos":gene.rightpos}
        data = json.dumps(dictionary)
        self.write(data)
        self.set_header('Content-type','json')
        self.finish()
        session.close()
        
class UniversalGeneHandler(BaseHandler):
    def get(self, geneId):
        session = Session()
        gene = session.query(Gene).filter(Gene.name == geneId).first()
        model_genes = session.query(Model_Gene).filter(Model_Gene.gene_id == gene.id).all()
        geneList = []
        dictionary = {}
        for mg in model_genes:
            model = session.query(Model).filter(Model.id == mg.model_id).first()
            geneList.append([model.biggid, gene.name])
        dictionary = {"biggid":gene.biggid, "genelist":geneList}
        data = json.dumps(dictionary)
        self.write(data)
        self.set_header('Content-type', 'json')
        self.finish()
        session.close()

class GeneListHandler(BaseHandler):
    def get(self, modelName):
        session = Session()
        geneList = GeneQuery().get_gene_list(modelName, session)
        data = json.dumps(sorted(geneList, key=lambda s: s.lower()))
        self.write(data)
        #self.set_header('Content-type','json')
        self.finish()
        session.close()

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
