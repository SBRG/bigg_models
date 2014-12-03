import smtplib
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
from ome.models import (Model, Component, Reaction,Compartment, Metabolite,
                        CompartmentalizedComponent, ModelReaction, ReactionMatrix,
                        GPRMatrix, ModelCompartmentalizedComponent, ModelGene, Gene, Comments, GenomeRegion, Genome)
from jinja2 import Environment, FileSystemLoader
from sqlalchemy.orm import sessionmaker, aliased
from sqlalchemy import create_engine, desc, func, or_
from contextlib import contextmanager
from collections import Counter
from queries import (ReactionQuery, ModelQuery, MetaboliteQuery,
                        GeneQuery, StringBuilder)

from download.sbml import sbmlio
#write_cobra_model_to_sbml_file(cobra_model, sbml_filename)

define("port", default= 8887, help="run on given port", type=int)

env = Environment(loader=FileSystemLoader('templates'))

directory = abspath(dirname(__file__))

urlBasePath = "http://localhost:8887/"

engine = create_engine("postgresql://dbuser@localhost:5432/ome_stage")

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
                    (r"/api/models/universal/reactions/(.*)$", UniversalReactionHandler),
                    (r"/models/universal/reactions/(.*)$", UniversalReactionDisplayHandler),
                    (r"/models/(.*)/reactions/(.*)$",ReactionDisplayHandler),
                    (r"/api/models/(.*)/reactions/(.*)$", ReactionHandler),
                    (r"/api/models/(.*)/reactions$", ReactionListHandler),
                    (r"/api/models/(.*)/genes/(.*)$", GeneHandler),
                    (r"/api/models/universal/metabolites/(.*)$", UniversalMetaboliteHandler),
                    (r"/models/universal/metabolites/(.*)$", UniversalMetaboliteDisplayHandler),
                    (r"/api/models/universal/metabolites/(.*)$", UniversalMetaboliteListHandler),
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
        useremail = self.get_argument("email", "empty")
        #keggid = self.get_argument("keggid", "empty")
        #casnumber = self.get_argument("casnumber", "empty")
        #name = self.get_argument("name", "empty")
        #formula = self.get_argument("formula", "empty")
        comments = self.get_argument("comments", "empty")
        commentobject = Comments(email = useremail, text = comments)
        session.add(commentobject)
        session.commit()
        session.close()
        #to = 'jslu@eng.ucsd.edu'
        to = email
        gmail_user = 'justinlu10@gmail.com'
        gmail_pwd = 'ultimate9'
        smtpserver = smtplib.SMTP("smtp.gmail.com", 587)
        smtpserver.ehlo()
        smtpserver.starttls()
        smtpserver.login(gmail_user, gmail_pwd)
        header = 'To:' + gmail_user + '\n' + 'From: ' +gmail_user + '\n' + 'Subject:BiGG comment notification \n'
        msg = header + comments + '\n ' + to
        smtpserver.sendmail(gmail_user, to, msg)
        smtpserver.close()
                
        
class DownloadPageHandler(BaseHandler):
    def get(self):
        template = env.get_template('download.html')
        input = self.get_argument("query")
        model = sbmlio.createSBML(input)
        dictionary = {"xml":model.id + ".xml"} #currently not implemented. Need script to convert database to coprapy object and then to sbml
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
            modellist.append([m.bigg_id , self.get_argument(m.bigg_id, "empty")])
        metaboliteradio = self.get_argument("metabolites", "empty")
        reactionradio = self.get_argument("reactions", "empty")
        generadio = self.get_argument("genes", "empty")
        genelist =[]
        reactionList = []
        reactions=[]
        metabolites=[]
        #model = session.query(Model).filter(Model.biggid.in_(modelradios.split(','))).all()
        metaboliteResults = []
        reactionResults = []
        geneResults = []
        modelResults = []
        similarityBoundary = str(.3)
        if metaboliteradio != "empty" or allradio !="empty":
        
            if input == "":
                for modelName in modellist:
                    model = session.query(Model).filter(Model.bigg_id == modelName[0]).first()
                    if modelName[1] != "empty":
                        metresult = session.query(Metabolite.id, Metabolite.name).join(CompartmentalizedComponent).join(ModelCompartmentalizedComponent).join(Model).filter(Model.bigg_id == modelName[0]).all()
                        for row in metresult:
                            for cc in session.query(CompartmentalizedComponent).filter(CompartmentalizedComponent.component_id == row.id).distinct(CompartmentalizedComponent.component_id).all():
                                for mcc in session.query(ModelCompartmentalizedComponent).filter(ModelCompartmentalizedComponent.compartmentalized_component_id ==cc.id).filter(ModelCompartmentalizedComponent.model_id == model.id).all():
                                    compartment = session.query(Compartment).join(CompartmentalizedComponent).filter(CompartmentalizedComponent.id == cc.id).first()
                                    metaboliteResults.append([model.bigg_id, row.name + "_"+compartment.name])
            else:
                metresult = session.query(Metabolite.id, Metabolite.name, func.similarity(Metabolite.name, str(input)).label("sim")).filter(Metabolite.name % str(input)).filter(func.similarity(Metabolite.name, str(input))> similarityBoundary).order_by(desc('sim')).all()
                for modelName in modellist:
                    model = session.query(Model).filter(Model.bigg_id == modelName[0]).first()
                    if modelName[1] != "empty":
                    
                        for row in metresult:
                            for cc in session.query(CompartmentalizedComponent).filter(CompartmentalizedComponent.component_id == row.id).distinct(CompartmentalizedComponent.component_id).all():
                                for mcc in session.query(ModelCompartmentalizedComponent).filter(ModelCompartmentalizedComponent.compartmentalized_component_id ==cc.id).filter(ModelCompartmentalizedComponent.model_id == model.id).all():
                                    compartment = session.query(Compartment).join(CompartmentalizedComponent).filter(CompartmentalizedComponent.id == cc.id).first()
                                    metaboliteResults.append([model.bigg_id, row.name + "_"+compartment.name]) 
                    """
                    metaboliteList = MetaboliteQuery().get_metabolite_list(modelName[0], session)
                    for metab in metaboliteList:
                        metaboliteResults.append([modelName[0], metab[0] + "_"+metab[1]])"""
        if reactionradio != "empty" or allradio !="empty":
            if input == "":
                for modelName in modellist:
                    if modelName[1] != "empty":
                        reacresult = session.query(Reaction.id, Reaction.name).join(ModelReaction).join(Model).filter(Model.bigg_id == modelName[0]).all()
                        for row in reacresult:
                            reactionResults.append([modelName[0], row.name])
            else:
                reacresult = session.query(Reaction.id, Reaction.name, func.similarity(Reaction.name, str(input)).label("sim")).filter(Reaction.name % str(input)).filter(func.similarity(Reaction.name, str(input))> similarityBoundary).order_by(desc('sim')).all()
                for modelName in modellist:
                    model = session.query(Model).filter(Model.bigg_id == modelName[0]).first()
                    if modelName[1] != "empty":
                        for row in reacresult:
                            reaction = session.query(Reaction).join(ModelReaction).join(Model).filter(Reaction.id == row.id).filter(Model.bigg_id == model.bigg_id).first()
                            if reaction != None:
                                reactionResults.append([modelName[0], reaction.name])
                                
        if generadio != "empty" or allradio !="empty":
            if input == "":
                for modelName in modellist:
                    if modelName[1] != "empty":
                        generesult = session.query(Gene.id, Gene.name).join(ModelGene).join(Model).filter(Model.bigg_id == modelName[0]).all()
                        for row in generesult:
                            geneResults.append([modelName[0], row.name])
            else:
                generesult = session.query(Gene.id, Gene.name, func.similarity(Gene.name, str(input)).label("sim")).filter(Gene.name % str(input)).filter(func.similarity(Gene.name, str(input))> similarityBoundary).order_by(desc('sim')).all()
                for modelName in modellist:
                    if modelName[1] != "empty":   
                        for row in generesult:
                            gene = session.query(Gene).join(ModelGene).join(Model).filter(Model.bigg_id == modelName[0]).filter(Gene.id == row.id).first()
                            if gene != None:
                                geneResults.append([modelName[0], gene.name])
           
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
        modelreaction = ReactionQuery().get_ModelReaction(reaction.id, modelquery.id, session).first()
        for rxn in session.query(ModelReaction).filter(ModelReaction.reaction_id == reaction.id).all():
            if rxn.model_id != modelquery.id:
                altModel = session.query(Model).filter(Model.id == rxn.model_id).first()
                altModelList.append(altModel.bigg_id)
        metabolitelist = ReactionQuery().get_metabolite_list(modelquery, reaction, session) 
        reaction_string = StringBuilder().build_reaction_string(metabolitelist, modelreaction)
        genelist = ReactionQuery().get_gene_list(reaction, modelquery, session)
        templist = modelreaction.gpr.replace("(","").replace(")","").split()
        genelist2 = [name for name in templist if name !="or" and name !="and"]
        sortedMetaboliteList = sorted(metabolitelist, key=lambda metabolite: metabolite[0])
        dictionary = {"model":modelquery.bigg_id, "name": reaction.name, "long_name": reaction.long_name, 
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
        request = tornado.httpclient.HTTPRequest(url=url_request, connect_timeout=20.0, request_timeout=20.0)
        response = yield gen.Task(http_client.fetch, request)
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
        request = tornado.httpclient.HTTPRequest(url=url_request, connect_timeout=20.0, request_timeout=20.0)
        response = yield gen.Task(http_client.fetch, request)
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
        ModelReactions = session.query(ModelReaction).filter(ModelReaction.reaction_id == reaction.id).all()
        for mr in ModelReactions:
            model = session.query(Model).filter(Model.id == mr.model_id).first()
            reaction = session.query(Reaction).filter(Reaction.id == mr.reaction_id).first()
            reactionList.append([model.bigg_id, reaction.name])
        dictionary = {"reactions":reactionList, "long_name":reaction.long_name, "name": reaction.name}
        data = json.dumps(dictionary)
        self.write(data)
        self.set_header('Content-type','json')
        self.finish()
        session.close()

class UniversalReactionDisplayHandler(BaseHandler):
    @asynchronous
    @gen.engine
    def get(self, reactionId):
        template = env.get_template("universalreactions.html")
        http_client = AsyncHTTPClient()
        url_request = 'http://localhost:%d/api/models/universal/reactions/%s' % (options.port, reactionId)
        request = tornado.httpclient.HTTPRequest(url=url_request, connect_timeout=20.0, request_timeout=20.0)
        response = yield gen.Task(http_client.fetch, request)
        results = json.loads(response.body)
        self.write(template.render(results))
        self.set_header('Content-type','text/html')
        self.finish()  
        
class SearchHandler(BaseHandler):
    def get(self):
        session = Session()
        similarityBoundary = str(.3)
        input = str(self.get_argument("query"))
        reactionlist = []
        metabolitelist = []
        modellist = []
        genelist = []
        
        result = session.query(Gene.id, Gene.locus_id, func.similarity(Gene.locus_id, str(input)).label("sim")).filter(Gene.locus_id % str(input)).filter(func.similarity(Gene.locus_id, str(input))>= str(1)).order_by(desc('sim')).all()
        for row in result:
            gene = session.query(Gene).filter(Gene.id == row.id).first()
            model_gene = session.query(ModelGene).filter(ModelGene.gene_id == row.id).first()
            if model_gene != None:
                model = session.query(Model).filter(Model.id == model_gene.model_id).first()
                genelist.append([model.bigg_id, gene.name])
        
        result = session.query(Reaction.id, Reaction.name, func.similarity(Reaction.name, str(input)).label("sim")).filter(Reaction.name % str(input)).filter(func.similarity(Reaction.name, str(input))> similarityBoundary).order_by(desc('sim')).all()
        for row in result:
            reactionlist.append(['universal',row.name])
               
        result = session.query(Metabolite.id, Metabolite.name, func.similarity(Metabolite.name, str(input)).label("sim")).filter(Metabolite.name % str(input)).filter(func.similarity(Metabolite.name, str(input))> similarityBoundary).order_by(desc('sim')).all()
        for row in result:
            metabolitelist.append(['universal',row.name])
        
        result = session.query(Genome.id, Genome.organism, func.similarity(Genome.organism, str(input)).label("sim")).filter(Genome.organism % str(input)).filter(func.similarity(Genome.organism, str(input))> similarityBoundary).order_by(desc('sim')).all()
        for row in result:
            
            modelquery = session.query(Model).filter(Model.genome_id == row.id)
            if modelquery.count():
                for model in modelquery.all():
                    templist = []
                    modelquery = ModelQuery().get_model(model.bigg_id, session)
                    reactionquery = ModelQuery().get_ModelReaction_count(modelquery, session)
                    metabolitequery = ModelQuery().get_model_metabolite_count(modelquery, session)
                    genequery = ModelQuery().get_gene_count(modelquery, session)
                    templist.extend([model.bigg_id, row.organism, metabolitequery, reactionquery, genequery]) 
                    modellist.append(templist)
        """
        result = session.query(Reaction.id, Reaction.name, func.similarity(Reaction.name, str(input)).label("sim")).filter(Reaction.name % str(input)).filter(func.similarity(Reaction.name, str(input))> similarityBoundary).order_by(desc('sim')).all()
        for row in result:
            for reaction in session.query(ModelReaction).filter(ModelReaction.reaction_id == row.id).all():   
                model = session.query(Model).filter(Model.id == reaction.model_id).first()
                reactionlist.append([model.bigg_id, row.name])
        
        result = session.query(Metabolite.id, Metabolite.name, func.similarity(Metabolite.name, str(input)).label("sim")).filter(Metabolite.name % str(input)).filter(func.similarity(Metabolite.name, str(input))> similarityBoundary).order_by(desc('sim')).all()
        for row in result:
            for cc in session.query(CompartmentalizedComponent).filter(CompartmentalizedComponent.component_id == row.id).distinct(CompartmentalizedComponent.component_id).all():
                for mcc in session.query(Model_CompartmentalizedComponent).filter(Model_CompartmentalizedComponent.CompartmentalizedComponent_id ==cc.id).all():
                    
                    model = session.query(Model).filter(Model.id == mcc.model_id).first()
                    compartment = session.query(Compartment).join(CompartmentalizedComponent).filter(CompartmentalizedComponent.id == cc.id).first()
                    metabolitelist.append([model.bigg_id, row.name + "_"+compartment.name]) 
        """
        result = session.query(Model.id, Model.bigg_id, func.similarity(Model.bigg_id, str(input)).label("sim")).filter(Model.bigg_id % str(input)).filter(func.similarity(Model.bigg_id, str(input))> similarityBoundary).order_by(desc('sim')).all()
        for row in result:
            templist = []
            modelquery = ModelQuery().get_model(row.bigg_id, session)
            reactionquery = ModelQuery().get_ModelReaction_count(modelquery, session)
            metabolitequery = ModelQuery().get_model_metabolite_count(modelquery, session)
            genequery = ModelQuery().get_gene_count(modelquery, session)
            genomequery = session.query(Genome).filter(Genome.id == modelquery.genome_id).first()
            templist.extend([row.bigg_id, genomequery.organism, metabolitequery, reactionquery, genequery]) 
            modellist.append(templist)
        result = session.query(Gene.id, Gene.name, func.similarity(Gene.name, str(input)).label("sim")).filter(Gene.name % str(input)).filter(func.similarity(Gene.name, str(input))> similarityBoundary).order_by(desc('sim')).all()
        for row in result:
            model_gene = session.query(ModelGene).filter(ModelGene.gene_id == row.id).first()
            if model_gene != None:
                model = session.query(Model).filter(Model.id == model_gene.model_id).first()
                genelist.append([model.bigg_id, row.name])
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
        url_request = 'http://localhost:%d/api/search?query=%s' % (options.port, self.get_argument("query").replace (" ", "+"))
        request = tornado.httpclient.HTTPRequest(url=url_request, connect_timeout=20.0, request_timeout=20.0)
        response = yield gen.Task(http_client.fetch, request)
        
        results = json.loads(response.body)
        self.write(template.render(results))
        self.set_header('Content-type','text/html')
        self.finish() 
    
class AutoCompleteHandler(BaseHandler):
    def get(self):
        session = Session()
        similarityBoundary = str(.2)
        
        input = self.get_argument("query") 
        resultlist = []
        
        result = session.query(Reaction.name, func.similarity(Reaction.name, str(input)).label("sim")).filter(Reaction.name % str(input)).filter(func.similarity(Reaction.name, str(input))> similarityBoundary).all()
        for row in result:
            resultlist.append([row.name,row.sim])
            
        result = session.query(Gene.locus_id, func.similarity(Gene.locus_id, str(input)).label("sim")).join(ModelGene).distinct().filter(Gene.locus_id % str(input)).filter(func.similarity(Gene.locus_id, str(input))> str(.5)).all()
        for row in result:
            resultlist.append([row.locus_id, row.sim])
          
        result = session.query(Genome.organism, func.similarity(Genome.organism, str(input)).label("sim")).filter(Genome.organism % str(input)).filter(func.similarity(Genome.organism, str(input))> similarityBoundary).group_by(Genome.organism).all()
        for row in result:
            resultlist.append([row.organism,row.sim])
                   
        result = session.query(Metabolite.name, func.similarity(Metabolite.name, str(input)).label("sim")).filter(Metabolite.name % str(input)).filter(func.similarity(Metabolite.name, str(input))> similarityBoundary).all()
        for row in result:
            resultlist.append([row.name,row.sim]) 
        
        result = session.query(Model.bigg_id, func.similarity(Model.bigg_id, str(input)).label("sim")).filter(Model.bigg_id % str(input)).filter(func.similarity(Model.bigg_id, str(input))> similarityBoundary).all()   
        for row in result:
            resultlist.append([row.bigg_id,row.sim]) 
        #distinctGene =aliased(Gene, func.distinct(Gene.name))
        result = session.query(Gene.name, func.similarity(Gene.name, str(input)).label("sim")).join(ModelGene).filter(Gene.name % str(input)).filter(func.similarity(Gene.name, str(input))> similarityBoundary).group_by(Gene.name).all()
        for row in result:
            
            #if i join with ModelGene then I should not have to check for model existence in gene
            resultlist.append([row.name,row.sim])  
        session.close()
        x = 0
        dictionary = {}
        #joinedlist = reactionlist + metabolitelist + modellist + genelist + organismlist + locuslist
        sortedResultList = sorted(resultlist, key=lambda query: query[1], reverse=True)
        for result in sortedResultList:
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
            reactionquery = ModelQuery().get_ModelReaction_count(modelquery, session)
            metabolitequery = ModelQuery().get_model_metabolite_count(modelquery, session)
            genequery = ModelQuery().get_gene_count(modelquery, session)
            genomequery = session.query(Genome).filter(Genome.id == modelquery.genome_id).first()
            dictionary = {"model":modelquery.bigg_id,"reaction_count":reactionquery,"metabolite_count":metabolitequery,
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
        request = tornado.httpclient.HTTPRequest(url=url_request, connect_timeout=20.0, request_timeout=20.0)
        response = yield gen.Task(http_client.fetch, request)
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
            reactionquery = ModelQuery().get_ModelReaction_count(modelquery, session)
            metabolitequery = ModelQuery().get_model_metabolite_count(modelquery, session)
            genequery = ModelQuery().get_gene_count(modelquery, session)
            genomequery = session.query(Genome).filter(Genome.id == modelquery.genome_id).first()
            templist.extend([modelquery.bigg_id, genomequery.organism, metabolitequery, reactionquery,  genequery])
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
        modelquery = session.query(Model).filter(Model.bigg_id == modelName).first()
        componentquery = session.query(Metabolite).filter(Metabolite.name == metaboliteId.split("_")[0]).first()
        compartmentquery = session.query(Compartment).filter(Compartment.name == metaboliteId[-1:len(metaboliteId)]).first()
        metabolitequery = session.query(Metabolite).filter(componentquery.id == Metabolite.id).first()
        compartmentlist = []
        altModelList = []
        for cc in session.query(CompartmentalizedComponent).filter(CompartmentalizedComponent.component_id == componentquery.id).filter(CompartmentalizedComponent.compartment_id == compartmentquery.id).all():         
            for mcc in session.query(ModelCompartmentalizedComponent).filter(ModelCompartmentalizedComponent.compartmentalized_component_id == cc.id).all():
                if mcc.model_id != modelquery.id:
                    altModel = session.query(Model).filter(Model.id == mcc.model_id).first()
                    altModelList.append(str(altModel.bigg_id))                   
        reactionlist = []
        for x in MetaboliteQuery().get_ModelReactions(componentquery.name, compartmentquery.name, modelquery, session):
            reactionlist.append(str(x.name))
               
        sortedReactionList = sorted(reactionlist)
        dictionary = {'name': str(componentquery.long_name), 'id': metaboliteId, 'universalname':componentquery.name, 'cas_number':str(metabolitequery.cas_number), 'seed':str(metabolitequery.seed),
        'metacyc':str(metabolitequery.metacyc),'brenda':str(metabolitequery.brenda), 'upa':str(metabolitequery.upa), 'chebi':str(metabolitequery.chebi), 'kegg_id': metabolitequery.kegg_id,'reactions':reactionlist, 'model': str(modelquery.bigg_id), 'formula': str(metabolitequery.formula), "altModelList": altModelList}
        data = json.dumps(dictionary)
        
        self.write(data)
        self.set_header('Content-type','json')
        self.finish()
        session.close()
        
class UniversalMetaboliteListHandler(BaseHandler):
    def get(self):
        session = Session()
        [x.name for x in (sessionquery(Metabolite).all())]

class UniversalMetaboliteHandler(BaseHandler):
    def get(self, metaboliteId):
        session = Session()
        componentquery = session.query(Metabolite).filter(Metabolite.name == metaboliteId).first()
        compartmentList = ['c', 'e', 'p']
        
        metaboliteList = []
        for c in compartmentList:
            temp_metaboliteList = []
            model_components = session.query(ModelCompartmentalizedComponent).join(CompartmentalizedComponent).join(Compartment).filter(CompartmentalizedComponent.compartment_id == Compartment.id).filter(CompartmentalizedComponent.component_id == componentquery.id).filter(Compartment.name == c).all()
            for mc in model_components:
                model = session.query(Model).filter(Model.id == mc.model_id).first()
                compartment = session.query(Compartment).filter(Compartment.id == mc.compartment_id).first()
                temp_metaboliteList.append([model.bigg_id, componentquery.name, compartment.name])
            metaboliteList.append(temp_metaboliteList)
        reactionList = []
        for c in compartmentList:
            temp_reactionList = [(x[0].name, x[1].bigg_id) for x in (session
                .query(Reaction, Model)
                .join(ModelReaction)
                .join(Model)
                .join(ReactionMatrix)
                .join(CompartmentalizedComponent)
                .join(Compartment)
                .join(Component)
                .join(Metabolite)
                .filter(Compartment.name == c)
                .filter(Metabolite.name == metaboliteId)
                .all())]
            reactionList.append([c, temp_reactionList])
        
        dictionary = {'long_name':str(componentquery.long_name), 'name': str(componentquery.name), 'kegg_id': str(componentquery.kegg_id), 'cas_number':str(componentquery.cas_number), 'seed':str(componentquery.seed),
        'metacyc':str(componentquery.metacyc), 'upa':str(componentquery.upa), 'brenda':str(componentquery.brenda),'chebi':str(componentquery.chebi), 
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
        url_request = 'http://localhost:%d/api/models/universal/metabolites/%s' % (options.port, metaboliteId)
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
        request = tornado.httpclient.HTTPRequest(url=url_request, connect_timeout=20.0, request_timeout=20.0)
        response = yield gen.Task(http_client.fetch, request)
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
        request = tornado.httpclient.HTTPRequest(url=url_request, connect_timeout=20.0, request_timeout=20.0)
        response = yield gen.Task(http_client.fetch, request)
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
        request = tornado.httpclient.HTTPRequest(url=url_request, connect_timeout=20.0, request_timeout=20.0)
        response = yield gen.Task(http_client.fetch, request)
        dictionary = {"geneResults":json.loads(response.body),"Genes":"Genes", "model":modelName}
        self.write(template.render(dictionary))
        self.set_header('Content-type','text/html') 
        self.finish()
 
class GeneHandler(BaseHandler):
    def get(self,modelName,geneName):
        session = Session()
        reactionList = []
        altModelList = []
        gene = session.query(Gene).join(ModelGene).join(Model).filter(Gene.name==geneName).filter(Model.bigg_id == modelName).first()
        #gene = session.query(Gene).filter(Gene.id == geneRegion.id).first()
        """
        for gm in session.query(ModelGene).filter(ModelGene.gene_id == gene.id).all():
            model = session.query(Model).filter(Model.id == gm.model_id).first()
            if model.bigg_id != modelName:
                altModelList.append(model.bigg_id)
        """
        for instance in GeneQuery().get_ModelReaction(geneName, session):
            model = GeneQuery().get_model(instance, session)
            geneList = []
            if model.bigg_id == modelName:
                list = []
                list.append(instance.name)
                list.append(instance.gpr)
                for x in session.query(Gene).join(ModelGene).join(GPRMatrix).filter(GPRMatrix.model_reaction_id == instance.id):
                    geneList.append([x.name,x.locus_id])
                list.append(geneList)
                #geneList = instance.gpr.replace("(","").replace(")","").split()
                #list.append([name for name in geneList if name !="or" and name !="and"])
                reactionList.append(list)       
        dictionary = {"name": geneName,"id":gene.locus_id, "model":modelName, "reactions": reactionList, "info":gene.info, "leftpos":gene.leftpos,"rightpos":gene.rightpos}
        data = json.dumps(dictionary)
        self.write(data)
        self.set_header('Content-type','json')
        self.finish()
        session.close()
"""       
class UniversalGeneHandler(BaseHandler):
    def get(self, geneId):
        session = Session()
        gene = session.query(Gene).filter(Gene.name == geneId).first()
        ModelGenes = session.query(ModelGene).filter(ModelGene.gene_id == gene.id).all()
        geneList = []
        dictionary = {}
        for mg in ModelGenes:
            model = session.query(Model).filter(Model.id == mg.model_id).first()
            geneList.append([model.bigg_id, gene.name])
        dictionary = {"biggid":gene.bigg_id, "genelist":geneList}
        data = json.dumps(dictionary)
        self.write(data)
        self.set_header('Content-type', 'json')
        self.finish()
        session.close()
"""
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
        request = tornado.httpclient.HTTPRequest(url=url_request, connect_timeout=20.0, request_timeout=20.0)
        response = yield gen.Task(http_client.fetch, request)
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
