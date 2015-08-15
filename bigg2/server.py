import smtplib
import tornado.ioloop
import tornado.web
import tornado.httpserver
from tornado.options import define, options
from tornado.escape import url_escape
from tornado.web import (StaticFileHandler, RequestHandler, RedirectHandler,
                         asynchronous, HTTPError)
from tornado.httpclient import AsyncHTTPClient
from tornado import gen
from os.path import abspath, dirname, join, isfile, getsize
from jinja2 import Environment, PackageLoader
from sqlalchemy.orm import sessionmaker, aliased, Bundle
from sqlalchemy import create_engine, desc, func, or_
from collections import Counter
import simplejson as json
import subprocess
import os
import mimetypes

from bigg2 import queries
from bigg2.queries import NotFoundError
from ome import settings
from ome.models import (Model, Component, Reaction, Compartment, Metabolite,
                        CompartmentalizedComponent, ModelReaction,
                        ReactionMatrix, GeneReactionMatrix,
                        ModelCompartmentalizedComponent, ModelGene, Gene,
                        Comments, GenomeRegion, Genome)
from ome.base import Session
from ome.loading.model_loading.parse import split_compartment
import ome
import datetime

# command line options
define("port", default= 8888, help="run on given port", type=int)
define("password", default= "", help="password to email", type=str)
define('debug', default=False, help='Start server in debug mode')

# set up jinja2 template location
env = Environment(loader=PackageLoader('bigg2', 'templates'),
                  extensions=['jinja2.ext.with_'])

# root directory
directory = abspath(dirname(__file__))
static_model_dir = join(directory, "static", "models")

# api version
api_v = 'v2'
api_host = 'bigg.ucsd.edu'

# content types


# make a tutorial on how to make a api request using curl
# http://www.restapitutorial.com/

# -------------------------------------------------------------------------------
# Application API
# -------------------------------------------------------------------------------

def get_application(debug=False):
    return tornado.web.Application([
        (r'/', MainHandler),
        #
        # Universal
        #
        (r'/api/%s/(?:models/)?universal/reactions/?$' % api_v, UniversalReactionListHandler),
        (r'/(?:models/)?universal/reactions/?$', UniversalReactionListDisplayHandler),
        #
        (r'/api/%s/(?:models/)?universal/reactions/([^/]+)/?$' % api_v, UniversalReactionHandler),
        (r'/(?:models/)?universal/reactions/([^/]+)/?$', UniversalReactionDisplayHandler),
        #
        (r'/api/%s/(?:models/)?universal/metabolites/?$' % api_v, UniversalMetaboliteListHandler),
        (r'/(?:models/)?universal/metabolites/?$', UniversalMetaboliteListDisplayHandler),
        #
        (r'/api/%s/(?:models/)?universal/metabolites/([^/]+)/?$' % api_v, UniversalMetaboliteHandler),
        (r'/(?:models/)?universal/metabolites/([^/]+)/?$', UniversalMetaboliteDisplayHandler),
        #
        (r'/api/%s/compartments/?$' % api_v, CompartmentListHandler),
        (r'/compartments/?$', CompartmentListDisplayHandler),
        #
        (r'/api/%s/compartments/([^/]+)/?$' % api_v, CompartmentHandler),
        (r'/compartments/([^/]+)/?$', CompartmentDisplayHandler),
        #
        (r'/api/%s/genomes/?$' % api_v, GenomeListHandler),
        (r'/genomes/?$', GenomeListDisplayHandler),
        #
        (r'/api/%s/genomes/([^/]+)/?$' % api_v, GenomeHandler),
        (r'/genomes/([^/]+)/?$', GenomeDisplayHandler),
        #
        # By model
        #
        (r'/api/%s/models/?$' % api_v, ModelListHandler),
        (r'/models/?$', ModelsListDisplayHandler),
        #
        (r'/api/%s/models/([^/]+)/?$' % api_v, ModelHandler),
        (r'/models/([^/]+)/?$', ModelDisplayHandler),
        #
        (r'/(?:api/%s/)?models/([^/]+)/download/?$' % api_v, ModelDownloadHandler),
        #
        (r'/api/%s/models/([^/]+)/reactions/([^/]+)/?$' % api_v, ReactionHandler),
        (r'/models/([^/]+)/reactions/([^/]+)/?$', ReactionDisplayHandler),
        #
        (r'/api/%s/models/([^/]+)/reactions/?$' % api_v, ReactionListHandler),
        (r'/models/([^/]+)/reactions/?$', ReactionListDisplayHandler),
        #
        (r'/api/%s/models/([^/]+)/metabolites/?$' % api_v, MetaboliteListHandler),
        (r'/models/([^/]+)/metabolites/?$', MetabolitesListDisplayHandler),
        #
        (r'/api/%s/models/([^/]+)/metabolites/([^/]+)/?$' % api_v, MetaboliteHandler),
        (r'/models/([^/]+)/metabolites/([^/]+)/?$', MetaboliteDisplayHandler),
        #
        (r'/api/%s/models/([^/]+)/genes/([^/]+)/?$' % api_v, GeneHandler),
        (r'/models/([^/]+)/genes/([^/]+)/?$', GeneDisplayHandler),
        #
        (r'/api/%s/models/([^/]+)/genes/?$' % api_v, GeneListHandler),
        (r'/models/([^/]+)/genes/?$', GeneListDisplayHandler),
        #
        # Search
        (r'/api/%s/search$' % api_v, SearchHandler),
        (r'/search$', SearchDisplayHandler),
        (r'/advanced_search$', AdvancedSearchHandler),
        (r'/advanced_search_external_id_results$', AdvancedSearchExternalIDHandler),
        (r'/advanced_search_results$', AdvancedSearchResultsHandler),
        (r'/linkout_advance_search_results$', LinkoutAdvanceSearchResultsHandler),
        (r'/autocomplete$', AutocompleteHandler),
        #
        # Maps
        (r'/escher_map_json/([^/]+)$', EscherMapJSONHandler),
        #
        # Comments
        (r'/submiterror$', SubmitErrorHandler),
        #
        # Pages
        (r'/web_api$', WebAPIHandler),
        (r'/license$', LicenseHandler),
        #
        # Static/Download
        (r'/static/(.*)$', StaticFileHandlerWithEncoding, {'path': join(directory, 'static')}),
        #
        # redirects
        (r'/multiecoli/?$', RedirectHandler, {'url': 'http://bigg1.ucsd.edu/multiecoli'})
    ], debug=debug)


def run(public=True):
    """Run the server"""

    tornado.options.parse_command_line()
    debug = options.debug
    http_server = tornado.httpserver.HTTPServer(get_application(debug=debug))
    print('serving BiGG 2 on port %d' % options.port)
    http_server.listen(options.port, None if public else "localhost")
    try:
        tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        print("bye!")


def stop():
    """Stop the server"""
    tornado.ioloop.IOLoop.instance().stop()


# -------------------------------------------------------------------------------
# Handlers
# -------------------------------------------------------------------------------


class BiggStaticFileHandler(StaticFileHandler):
    """This is sets the Content-Type for the various model formats

    This is mainly for testing. In production, the /static path should be
    handled by nginx or apache"""
    def get_content_type(self):
        path = self.absolute_path
        # need to fix type for gzip files until tornado patched
        # https://github.com/tornadoweb/tornado/pull/1468
        if path.endswith(".xml.gz"):
            return "application/gzip"
        # mat needs to be binary
        elif path.endswith(".mat"):
            return "application/octet-stream"
        else:
            return StaticFileHandler.get_content_type(self)


def _possibly_compartmentalized_met_id(obj):
    if 'compartment_bigg_id' not in obj:
        return obj['bigg_id']
    else:
        return '{bigg_id}_{compartment_bigg_id}'.format(**obj)


def _parse_col_arg(s):
    try:
        return s.split(',')
    except AttributeError:
        return None


def _get_col_name(query_arguments, columns, default_column=None,
                  default_direction='ascending'):
    for k, v in query_arguments.iteritems():
        split = [x.strip('[]') for x in k.split('[')]
        if len(split) != 2:
            continue
        if split[0] == 'col':
            sort_direction = ('ascending' if v[0] == '0' else 'descending')
            sort_col_index = int(split[1])
            return columns[sort_col_index], sort_direction
    return default_column, default_direction


def safe_query(func, *args, **kwargs):
    """Run the given function, and raise a 404 if it fails.

    Arguments
    ---------

    func: The function to run. *args and **kwargs are passed to this function.

    """
    session = Session()
    kwargs["session"] = session
    try:
        return func(*args, **kwargs)
    except queries.NotFoundError as e:
        raise HTTPError(status_code=404, reason=e.message)
    finally:
        session.close()


class BaseHandler(RequestHandler):
    def set_content_type(self, category):
        """Add a content type for 'html' or 'json'."""
        if category == 'html':
            self.set_header('Content-type', 'text/html; charset=utf-8')
        elif category == 'json':
            self.set_header('Content-type', 'application/json; charset=utf-8')
        else:
            raise Exception('Bad content type category %s' % category)


class MainHandler(BaseHandler):
    def get(self):
        template = env.get_template('index.html')
        self.write(template.render())
        self.set_content_type('html')
        self.finish()


# reactions
class UniversalReactionListHandler(BaseHandler):
    def get(self):
        # get arguments
        page = self.get_argument('page', None)
        size = self.get_argument('size', None)
        include_link_urls = (self.get_argument('include_link_urls', None) is not None)

        # defaults
        sort_column = 'bigg_id'
        sort_direction = 'ascending'

        # get the sorting column
        columns = _parse_col_arg(self.get_argument('columns', None))
        sort_column, sort_direction = _get_col_name(self.request.query_arguments, columns,
                                                    sort_column, sort_direction)

        # run the queries
        session = Session()
        raw_results = queries.get_universal_reactions(session, page, size,
                                                      sort_column, sort_direction)
        if include_link_urls:
            raw_results = [dict(x, link_urls={'bigg_id': '/universal/reactions/{bigg_id}'.format(**x)})
                           for x in raw_results]
        result = {'results': [dict(x, model_bigg_id='Universal') for x in raw_results],
                  'results_count': queries.get_universal_reactions_count(session)}
        session.close()

        # write out the JSON
        data = json.dumps(result)
        self.write(data)
        self.set_content_type('json')
        self.finish()


class UniversalReactionListDisplayHandler(BaseHandler):
    @asynchronous
    @gen.coroutine
    def get(self):
        template = env.get_template("list_display.html")
        dictionary = {'results': {'reactions': 'ajax'},
                      'hide_organism': True}
        self.write(template.render(dictionary))
        self.set_content_type('html')
        self.finish()


class UniversalReactionHandler(BaseHandler):
    def get(self, reaction_bigg_id):
        session = Session()
        # get the reaction object
        try:
            result = queries.get_reaction_and_models(reaction_bigg_id, session)
        except NotFoundError:
            raise HTTPError(404)
        session.close()

        data = json.dumps(result)
        self.write(data)
        self.set_content_type('json')
        self.finish()


class UniversalReactionDisplayHandler(BaseHandler):
    @asynchronous
    @gen.coroutine
    def get(self, reaction_bigg_id):
        template = env.get_template("universal_reaction.html")
        http_client = AsyncHTTPClient()
        url_request = ('http://localhost:%d/api/%s/models/universal/reactions/%s' %
                       (options.port, api_v, url_escape(reaction_bigg_id, plus=False)))
        request = tornado.httpclient.HTTPRequest(url=url_request,
                                                 connect_timeout=20.0,
                                                 request_timeout=20.0)
        response = yield gen.Task(http_client.fetch, request)
        if response.error:
            raise HTTPError(404)
        results = json.loads(response.body)
        self.write(template.render(results))
        self.set_content_type('html')
        self.finish()


class UniversalMetaboliteListHandler(BaseHandler):
    def get(self):
        # get arguments
        page = self.get_argument('page', None)
        size = self.get_argument('size', None)
        include_link_urls = (self.get_argument('include_link_urls', None) is not None)

        # defaults
        sort_column = 'bigg_id'
        sort_direction = 'ascending'

        # get the sorting column
        columns = _parse_col_arg(self.get_argument('columns', None))
        sort_column, sort_direction = _get_col_name(self.request.query_arguments, columns,
                                                    sort_column, sort_direction)

        # run the queries
        session = Session()
        raw_results = queries.get_universal_metabolites(session, page, size,
                                                        sort_column, sort_direction)
        # add links and universal
        if include_link_urls:
            raw_results = [dict(x, link_urls={'bigg_id': '/universal/metabolites/{bigg_id}'.format(**x)})
                           for x in raw_results]
        result = {'results': [dict(x, model_bigg_id='Universal') for x in raw_results],
                  'results_count': queries.get_universal_metabolites_count(session)}

        session.close()
        data = json.dumps(result)
        self.write(data)
        self.set_content_type('json')
        self.finish()


class UniversalMetaboliteListDisplayHandler(BaseHandler):
    @asynchronous
    @gen.coroutine
    def get(self):
        template = env.get_template("list_display.html")
        template_data = {'results': {'metabolites': 'ajax'},
                         'hide_organism': True}
        self.write(template.render(template_data))
        self.set_content_type('html')
        self.finish()


class UniversalMetaboliteHandler(BaseHandler):
    def get(self, met_bigg_id):
        results = safe_query(queries.get_metabolite, met_bigg_id)
        data = json.dumps(results)
        self.write(data)
        self.set_content_type('json')
        self.finish()


class UniversalMetaboliteDisplayHandler(BaseHandler):
    @asynchronous
    @gen.coroutine
    def get(self, met_bigg_id):
        template = env.get_template("universal_metabolite.html")
        http_client = AsyncHTTPClient()
        url_request = 'http://localhost:%d/api/%s/models/universal/metabolites/%s' % \
                      (options.port, api_v, url_escape(met_bigg_id, plus=False))
        response = yield gen.Task(http_client.fetch, url_request)
        if response.error:
            raise HTTPError(404)
        results = json.loads(response.body)
        self.write(template.render(results))
        self.set_content_type('html')
        self.finish()


class ReactionListHandler(BaseHandler):
    def get(self, model_bigg_id):
        # get arguments
        page = self.get_argument('page', None)
        size = self.get_argument('size', None)
        include_link_urls = (self.get_argument('include_link_urls', None) is not None)

        # defaults
        sort_column = 'bigg_id'
        sort_direction = 'ascending'

        # get the sorting column
        columns = _parse_col_arg(self.get_argument('columns', None))
        sort_column, sort_direction = _get_col_name(self.request.query_arguments, columns,
                                                    sort_column, sort_direction)

        # run the queries
        session = Session()
        raw_results = queries.get_model_reactions(model_bigg_id, session, page,
                                                  size, sort_column,
                                                  sort_direction)
        # add the URL
        if include_link_urls:
            raw_results = [dict(x, link_urls={'bigg_id': '/models/{model_bigg_id}/reactions/{bigg_id}'.format(**x)})
                           for x in raw_results]
        result = {'results': raw_results,
                  'results_count': queries.get_model_reactions_count(model_bigg_id, session)}

        session.close()
        self.write(json.dumps(result))
        self.set_content_type('json')
        self.finish()


class ReactionListDisplayHandler(BaseHandler):
    @asynchronous
    @gen.coroutine
    def get(self, model_bigg_id):
        template = env.get_template("list_display.html")
        template_data = {'results': {'reactions': 'ajax'}}
        self.write(template.render(template_data))
        self.set_content_type('html')
        self.finish()


class ReactionHandler(BaseHandler):
    def get(self, model_bigg_id, reaction_bigg_id):
        results = safe_query(queries.get_model_reaction,
                             model_bigg_id, reaction_bigg_id)
        data = json.dumps(results)
        self.write(data)
        self.set_content_type('json')
        self.finish()


class ReactionDisplayHandler(BaseHandler):
    @asynchronous
    @gen.coroutine
    def get(self, model_bigg_id, reaction_bigg_id):
        template = env.get_template("reaction.html")
        http_client = AsyncHTTPClient()
        url_request = 'http://localhost:%d/api/%s/models/%s/reactions/%s' % \
                      (options.port, api_v,
                       url_escape(model_bigg_id, plus=False),
                       url_escape(reaction_bigg_id, plus=False))
        request = tornado.httpclient.HTTPRequest(url=url_request,
                                                 connect_timeout=20.0,
                                                 request_timeout=20.0)
        response = yield gen.Task(http_client.fetch, request)
        if response.error:
            raise HTTPError(404)
        data = json.loads(response.body)
        for result in data['results']:
            result['reaction_string'] = queries.build_reaction_string(data['metabolites'],
                                                                      result['lower_bound'],
                                                                      result['upper_bound'])
        self.write(template.render(data))
        self.set_content_type('html')
        self.finish()


# Compartments
class CompartmentListHandler(BaseHandler):
    def get(self):
        session = Session()
        results = [{'bigg_id': x[0], 'name': x[1]}
                   for x in session.query(Compartment.bigg_id, Compartment.name).all()]
        session.close()

        data = json.dumps(results)
        self.write(data)
        self.set_content_type('json')
        self.finish()


class CompartmentListDisplayHandler(BaseHandler):
    @asynchronous
    @gen.coroutine
    def get(self):
        template = env.get_template("compartments.html")
        http_client = AsyncHTTPClient()
        url_request = 'http://localhost:%d/api/%s/compartments' % (options.port, api_v)
        request = tornado.httpclient.HTTPRequest(url=url_request,
                                                 connect_timeout=20.0,
                                                 request_timeout=20.0)
        response = yield gen.Task(http_client.fetch, request)
        if response.error:
            raise HTTPError(404)
        results = json.loads(response.body)
        self.write(template.render({'compartments': results,
                                    'no_pager': True}))
        self.set_content_type('html')
        self.finish()


class CompartmentHandler(BaseHandler):
    def get(self, compartment_bigg_id):
        session = Session()
        result_db = (session
                     .query(Compartment)
                     .filter(Compartment.bigg_id == compartment_bigg_id)
                     .first())
        session.close()

        result = {'bigg_id': result_db.bigg_id, 'name': result_db.name}
        data = json.dumps(result)
        self.write(data)
        self.set_content_type('json')
        self.finish()


class CompartmentDisplayHandler(BaseHandler):
    @asynchronous
    @gen.coroutine
    def get(self, compartment_bigg_id):
        template = env.get_template("compartment.html")
        http_client = AsyncHTTPClient()
        url_request = 'http://localhost:%d/api/%s/compartments/%s' % \
                      (options.port, api_v,
                       url_escape(compartment_bigg_id, plus=False))
        request = tornado.httpclient.HTTPRequest(url=url_request,
                                                 connect_timeout=20.0,
                                                 request_timeout=20.0)
        response = yield gen.Task(http_client.fetch, request)
        if response.error:
            raise HTTPError(404)
        results = json.loads(response.body)
        self.write(template.render(results))
        self.set_content_type('html')
        self.finish()


# Genomes
class GenomeListHandler(BaseHandler):
    def get(self):
        session = Session()
        results = [{'bioproject_id': x[0], 'organism': x[1]}
                   for x in session.query(Genome.bioproject_id, Genome.organism).all()]
        session.close()

        data = json.dumps(results)
        self.write(data)
        self.set_content_type('json')
        self.finish()


class GenomeListDisplayHandler(BaseHandler):
    @asynchronous
    @gen.coroutine
    def get(self):
        template = env.get_template("genomes.html")
        http_client = AsyncHTTPClient()
        url_request = 'http://localhost:%d/api/%s/genomes' % (options.port, api_v)
        request = tornado.httpclient.HTTPRequest(url=url_request,
                                                 connect_timeout=20.0,
                                                 request_timeout=20.0)
        response = yield gen.Task(http_client.fetch, request)
        if response.error:
            raise HTTPError(404)
        results = json.loads(response.body)
        self.write(template.render({'genomes': results}))
        self.set_content_type('html')
        self.finish()


class GenomeHandler(BaseHandler):
    def get(self, bioproject_id):
        session = Session()
        result = queries.get_genome_and_models(session, bioproject_id)
        session.close()

        data = json.dumps(result)
        self.write(data)
        self.set_content_type('json')
        self.finish()


class GenomeDisplayHandler(BaseHandler):
    @asynchronous
    @gen.coroutine
    def get(self, bioproject_id):
        template = env.get_template("genome.html")
        http_client = AsyncHTTPClient()
        url_request = 'http://localhost:%d/api/%s/genomes/%s' % \
                      (options.port, api_v, url_escape(bioproject_id, plus=False))
        request = tornado.httpclient.HTTPRequest(url=url_request,
                                                 connect_timeout=20.0,
                                                 request_timeout=20.0)
        response = yield gen.Task(http_client.fetch, request)
        if response.error:
            raise HTTPError(404)
        results = json.loads(response.body)
        self.write(template.render(results))
        self.set_content_type('html')
        self.finish()


# Models
class ModelListHandler(BaseHandler):
    def get(self):
        # get arguments
        page = self.get_argument('page', None)
        size = self.get_argument('size', None)
        include_link_urls = (self.get_argument('include_link_urls', None) is not None)

        # defaults
        sort_column = 'bigg_id'
        sort_direction = 'ascending'

        # get the sorting column
        columns = _parse_col_arg(self.get_argument('columns', None))
        sort_column, sort_direction = _get_col_name(self.request.query_arguments, columns,
                                                    sort_column, sort_direction)

        # run the queries
        session = Session()
        raw_results = queries.get_models(session, page, size, sort_column, sort_direction)
        if include_link_urls:
            raw_results = [dict(x, link_urls={'bigg_id': '/models/{bigg_id}'.format(**x),
                                              'metabolite_count': '/models/{bigg_id}/metabolites'.format(**x),
                                              'reaction_count': '/models/{bigg_id}/reactions'.format(**x),
                                              'gene_count': '/models/{bigg_id}/genes'.format(**x)})
                           for x in raw_results]
        result = {'results': raw_results,
                  'results_count': queries.get_models_count(session)}

        session.close()

        data = json.dumps(result)
        self.write(data)
        self.set_content_type('json')
        self.finish()


class ModelsListDisplayHandler(BaseHandler):
    @asynchronous
    @gen.coroutine
    def get(self):
        template = env.get_template("list_display.html")
        template_data = {'results': {'models': 'ajax'}}
        self.write(template.render(template_data))
        self.set_content_type('html')
        self.finish()


class ModelDownloadHandler(BaseHandler):
    def get(self, model_bigg_id):
        extension = self.get_argument("format", "json")
        self.redirect("/static/models/%s.%s" % (model_bigg_id, extension))


class ModelHandler(BaseHandler):
    def get(self, model_bigg_id):
        result = safe_query(queries.get_model_and_counts, model_bigg_id)
        # get filesizes
        for ext in ("xml", "mat", "json", "xml_gz"):
            fpath = join(static_model_dir,
                         model_bigg_id + "." + ext.replace("_", "."))
            byte_size = getsize(fpath) if isfile(fpath) else 0
            if byte_size > 1048576:
                result[ext + "_size"] = "%.1f MB" % (byte_size / 1048576.)
            elif byte_size > 1024:
                result[ext + "_size"] = "%.1f kB" % (byte_size / 1024.)
            elif byte_size > 0:
                result[ext + "_size"] = "%d B" % (byte_size)
        data = json.dumps(result)
        self.write(data)
        self.set_content_type('json')
        self.finish()


class ModelDisplayHandler(BaseHandler):
    @asynchronous
    @gen.coroutine
    def get(self, model_bigg_id):
        template = env.get_template("model.html")
        http_client = AsyncHTTPClient()
        url_request = 'http://localhost:%d/api/%s/models/%s' % \
                      (options.port, api_v, url_escape(model_bigg_id, plus=False))
        request = tornado.httpclient.HTTPRequest(url=url_request,
                                                 connect_timeout=20.0,
                                                 request_timeout=20.0)
        response = yield gen.Task(http_client.fetch, request)
        if response.error:
            raise HTTPError(404)
        results = json.loads(response.body)
        self.write(template.render(results))
        self.set_content_type('html')
        self.finish()


class MetaboliteListHandler(BaseHandler):
    def get(self, model_bigg_id):
        # get arguments
        page = self.get_argument('page', None)
        size = self.get_argument('size', None)
        include_link_urls = (self.get_argument('include_link_urls', None) is not None)

        # defaults
        sort_column = 'bigg_id'
        sort_direction = 'ascending'

        # get the sorting column
        columns = _parse_col_arg(self.get_argument('columns', None))
        sort_column, sort_direction = _get_col_name(self.request.query_arguments, columns,
                                                    sort_column, sort_direction)

        # run the queries
        session = Session()
        raw_results = queries.get_model_metabolites(model_bigg_id, session,
                                                    page, size, sort_column,
                                                    sort_direction)
        # add the URL
        if include_link_urls:
            raw_results = [dict(x, link_urls={'bigg_id': '/models/{model_bigg_id}/metabolites/{bigg_id}_{compartment_bigg_id}'.format(**x)})
                           for x in raw_results]
        result = {'results': raw_results,
                  'results_count': queries.get_model_metabolites_count(model_bigg_id, session)}

        session.close()
        data = json.dumps(result)

        self.write(data)
        self.set_content_type('json')
        self.finish()


class MetabolitesListDisplayHandler(BaseHandler):
    @asynchronous
    @gen.coroutine
    def get(self, model_bigg_id):
        template = env.get_template("list_display.html")
        http_client = AsyncHTTPClient()
        url_request = 'http://localhost:%d/api/%s/models/%s/metabolites' % \
                      (options.port, api_v, url_escape(model_bigg_id, plus=False))
        request = tornado.httpclient.HTTPRequest(url=url_request,
                                                 connect_timeout=20.0,
                                                 request_timeout=20.0)
        response = yield gen.Task(http_client.fetch, request)
        if response.error:
            raise HTTPError(404)
        dictionary = {"results": {"metabolites": json.loads(response.body)}}
        self.write(template.render(dictionary))
        self.set_content_type('html')
        self.finish()


class MetaboliteHandler(BaseHandler):
    def get(self, model_bigg_id, comp_met_id):
        met_bigg_id, compartment_bigg_id = split_compartment(comp_met_id)
        results = safe_query(queries.get_model_comp_metabolite,
                             met_bigg_id, compartment_bigg_id, model_bigg_id)

        data = json.dumps(results)
        self.write(data)
        self.set_content_type('json')
        self.finish()


class MetaboliteDisplayHandler(BaseHandler):
    @asynchronous
    @gen.coroutine
    def get(self, model_id, met_bigg_id):
        template = env.get_template("metabolite.html")
        http_client = AsyncHTTPClient()
        url_request = 'http://localhost:%d/api/%s/models/%s/metabolites/%s' % \
                      (options.port, api_v,
                       url_escape(model_id, plus=False),
                       url_escape(met_bigg_id, plus=False))
        request = tornado.httpclient.HTTPRequest(url=url_request,
                                                 connect_timeout=20.0,
                                                 request_timeout=20.0)
        response = yield gen.Task(http_client.fetch, request)
        if response.error:
            raise HTTPError(404)
        results = json.loads(response.body)
        self.write(template.render(results))
        self.set_content_type('html')
        self.finish()


class GeneListHandler(BaseHandler):
    def get(self, model_bigg_id):
        page = self.get_argument('page', None)
        size = self.get_argument('size', None)
        include_link_urls = (self.get_argument('include_link_urls', None) is not None)

        # defaults
        sort_column = 'bigg_id'
        sort_direction = 'ascending'

        # get the sorting column
        columns = _parse_col_arg(self.get_argument('columns', None))
        sort_column, sort_direction = _get_col_name(self.request.query_arguments, columns,
                                                    sort_column, sort_direction)

        # run the queries
        session = Session()
        raw_results = queries.get_model_genes(model_bigg_id, session, page,
                                              size, sort_column, sort_direction)

        # add the URL
        if include_link_urls:
            raw_results = [dict(x, link_urls={'bigg_id': '/models/{model_bigg_id}/genes/{bigg_id}'.format(**x)})
                           for x in raw_results]
        result = {'results': raw_results,
                  'results_count': queries.get_model_genes_count(model_bigg_id, session)}

        session.close()
        data = json.dumps(result)

        self.write(data)
        self.set_content_type('json')
        self.finish()


class GeneListDisplayHandler(BaseHandler):
    @asynchronous
    @gen.coroutine
    def get(self, model_bigg_id):
        template = env.get_template("list_display.html")
        template_data = {'results': {'genes': 'ajax'}}

        self.write(template.render(template_data))
        self.set_content_type('html')
        self.finish()


class GeneHandler(BaseHandler):
    def get(self, model_bigg_id, gene_bigg_id):
        result = safe_query(queries.get_model_gene,
                            gene_bigg_id, model_bigg_id)
        data = json.dumps(result)
        self.write(data)
        self.set_content_type('json')
        self.finish()


class GeneDisplayHandler(BaseHandler):
    @asynchronous
    @gen.coroutine
    def get(self, model_bigg_id, gene_bigg_id):
        template = env.get_template("gene.html")
        http_client = AsyncHTTPClient()
        url_request = 'http://localhost:%d/api/%s/models/%s/genes/%s' % \
                      (options.port, api_v,
                       url_escape(model_bigg_id, plus=False),
                       url_escape(gene_bigg_id, plus=False))
        request = tornado.httpclient.HTTPRequest(url=url_request,
                                                 connect_timeout=20.0,
                                                 request_timeout=20.0)
        response = yield gen.Task(http_client.fetch, request)
        if response.error:
            raise HTTPError(404)
        results = json.loads(response.body)
        self.write(template.render(results))
        self.set_content_type('html')
        self.finish()


class SearchHandler(BaseHandler):
    def get(self):
        # get arguments
        query_string = self.get_argument("query")
        page = self.get_argument('page', None)
        size = self.get_argument('size', None)
        search_type = self.get_argument('search_type', None)
        include_link_urls = (self.get_argument('include_link_urls', None) is not None)

        # defaults
        sort_column = None
        sort_direction = 'ascending'

        # get the sorting column
        columns = _parse_col_arg(self.get_argument('columns', None))
        sort_column, sort_direction = _get_col_name(self.request.query_arguments, columns,
                                                    sort_column, sort_direction)

        # run the queries
        session = Session()
        result = None

        if search_type == 'reactions':
            # reactions
            raw_results = queries.search_for_universal_reactions(query_string, session, page,
                                                                 size, sort_column, sort_direction)
            if include_link_urls:
                raw_results = [dict(x, link_urls={'bigg_id': '/universal/reactions/{bigg_id}'.format(**x)})
                               for x in raw_results]
            result = {'results': [dict(x, model_bigg_id='Universal', organism='') for x in raw_results],
                      'results_count': queries.search_for_universal_reactions_count(query_string,
                                                                                    session)}

        elif search_type == 'metabolites':
            raw_results = queries.search_for_universal_metabolites(query_string, session,
                                                                    page, size, sort_column,
                                                                    sort_direction)
            if include_link_urls:
                raw_results = [dict(x, link_urls={'bigg_id': '/universal/metabolites/{bigg_id}'.format(**x)})
                            for x in raw_results]

            result = {'results': [dict(x, model_bigg_id='Universal', organism='') for x in raw_results],
                      'results_count': queries.search_for_universal_metabolites_count(query_string, session)}

        elif search_type == 'genes':
            raw_results = queries.search_for_genes(query_string, session, page,
                                                   size, sort_column,
                                                   sort_direction)
            if include_link_urls:
                raw_results = [dict(x, link_urls={'bigg_id': '/models/{model_bigg_id}/genes/{bigg_id}'.format(**x)})
                               for x in raw_results]

            result = {'results': raw_results,
                      'results_count': queries.search_for_genes_count(query_string, session)}

        elif search_type == 'models':
            raw_results = queries.search_for_models(query_string, session, page,
                                                    size, sort_column, sort_direction)
            if include_link_urls:
                raw_results = [dict(x, link_urls={'bigg_id': '/models/{bigg_id}'.format(**x),
                                                'metabolite_count': '/models/{bigg_id}/metabolites'.format(**x),
                                                'reaction_count': '/models/{bigg_id}/reactions'.format(**x),
                                                'gene_count': '/models/{bigg_id}/genes'.format(**x)})
                               for x in raw_results]

            result = {'results': raw_results,
                      'results_count': queries.search_for_models_count(query_string, session)}

        else:
            raise HTTPError(400, 'Bad search_type %s' % search_type)

        session.close()
        data = json.dumps(result)
        self.write(data)

        self.set_content_type('json')
        self.finish()


class SearchDisplayHandler(BaseHandler):
    @asynchronous
    @gen.coroutine
    def get(self):
        template = env.get_template("list_display.html")
        template_data = {'results': {'models': 'ajax',
                                     'reactions': 'ajax',
                                     'metabolites': 'ajax',
                                     'genes': 'ajax'},
                         'tablesorter_size': 20}
        self.write(template.render(template_data))
        self.set_content_type('html')
        self.finish()


class AdvancedSearchHandler(BaseHandler):
    def get(self):
        template = env.get_template('advanced_search.html')
        session = Session()
        model_list = queries.get_model_list(session)
        database_sources = queries.get_database_sources(session)
        session.close()

        self.write(template.render({'models': model_list,
                                    'database_sources': database_sources}))
        self.set_content_type('html')
        self.finish()


class LinkoutAdvanceSearchResultsHandler(BaseHandler):
    def post(self):
        template = env.get_template("list_display.html")
        query_string = self.get_argument('query', None)
        external_id = self.get_argument("linkout_choice", None)

        session = Session()
        metabolite_results = queries.search_for_metabolites_by_external_id(query_string, external_id, session)
        dictionary = {'results': {'metabolites': metabolite_results}}
        session.close()

        self.write(template.render(dictionary))
        self.set_content_type('html')
        self.finish()


class AdvancedSearchExternalIDHandler(BaseHandler):
    def post(self):
        query_string = self.get_argument('query', '')
        database_source = self.get_argument('database_source', '')
        session = Session()
        metabolites = queries.get_metabolites_for_database_id(session,
                                                              query_string,
                                                              database_source)
        session.close()
        dictionary = {'results': {'metabolites': metabolites},
                      'no_pager': True,
                      'hide_organism': True}

        template = env.get_template("list_display.html")
        self.write(template.render(dictionary))
        self.set_content_type('html')
        self.finish()


class AdvancedSearchResultsHandler(BaseHandler):
    def post(self):
        query_strings = [x.strip() for x in
                         self.get_argument('query', '').split(',')
                         if x != '']
        # run the queries
        session = Session()
        def checkbox_arg(name):
            return self.get_argument(name, None) == 'on'


        all_models = queries.get_model_list(session)
        model_list = [m for m in all_models if checkbox_arg(m)]
        include_metabolites = checkbox_arg('include_metabolites')
        include_reactions = checkbox_arg('include_reactions')
        include_genes = checkbox_arg('include_genes')
        metabolite_results = []
        reaction_results = []
        gene_results = []

        # genes
        for query_string in query_strings:
            if include_genes:
                gene_results += queries.search_for_genes(query_string, session,
                                                         limit_models=model_list)
            if include_reactions:
                reaction_results += queries.search_for_reactions(query_string, session,
                                                                 limit_models=model_list)
            if include_metabolites:
                metabolite_results += queries.search_for_metabolites(query_string, session,
                                                                     limit_models=model_list)
        result = {'results': {'reactions': reaction_results,
                              'metabolites': metabolite_results,
                              'genes': gene_results},
                  'no_pager': True}

        session.close()
        template = env.get_template("list_display.html")
        self.write(template.render(result))
        self.set_content_type('html')
        self.finish()


class AutocompleteHandler(BaseHandler):
    def get(self):
        query_string = self.get_argument("query")

        # get the session
        session = Session()
        result_array = queries.search_ids_fast(query_string, session, limit=15)
        session.close()

        self.write(json.dumps(result_array))
        self.set_content_type('json')
        self.finish()


class EscherMapJSONHandler(BaseHandler):
    def get(self, map_name):
        session = Session()
        map_json = queries.json_for_map(map_name, session)
        session.close()

        self.write(map_json)
        self.set_content_type('json')
        self.finish()


class SubmitErrorHandler(BaseHandler):
    def post(self):
        session = Session()
        useremail = self.get_argument("email", "empty")
        comments = self.get_argument("comments", "empty")
        type = self.get_argument("type", "empty")
        weburl = self.get_argument("url", "empty")
        now = datetime.datetime.now()
        commentobject = Comments(email=useremail, text=comments,
                                 date_created=now, type=type, url=weburl)
        session.add(commentobject)
        session.commit()
        session.close()


class WebAPIHandler(BaseHandler):
    def get(self):
        template = env.get_template('web_api.html')
        self.write(template.render(api_host=api_host))
        self.set_content_type('html')
        self.finish()


class LicenseHandler(BaseHandler):
    def get(self):
        template = env.get_template('about_license_page.html')
        self.write(template.render())
        self.set_content_type('html')
        self.finish()


# static files
class StaticFileHandlerWithEncoding(StaticFileHandler):
    # This is only to opportunisticly use a pre-compressed file
    # (equivalent to gzip_static in nginx).
    def get_absolute_path(self, root, path):
        p = abspath(join(root, path))
        # if the client accepts gzip
        if "gzip" in self.request.headers.get('Accept-Encoding', ''):
            if isfile(p + ".gz"):
                self.set_header("Content-Encoding", "gzip")
                return p + ".gz"
        return p

    def get_content_type(self):
        """Same as the default, except that we add a utf8 encoding for XML and JSON files."""
        mime_type, encoding = mimetypes.guess_type(self.path)

        # from https://github.com/tornadoweb/tornado/pull/1468
        # per RFC 6713, use the appropriate type for a gzip compressed file
        if encoding == "gzip":
            return "application/gzip"
        # As of 2015-07-21 there is no bzip2 encoding defined at
        # http://www.iana.org/assignments/media-types/media-types.xhtml
        # So for that (and any other encoding), use octet-stream.
        elif encoding is not None:
            return "application/octet-stream"

        # assume utf-8 for xml and json
        elif mime_type == 'application/xml':
            return 'application/xml; charset=utf-8'
        elif mime_type == 'application/json':
            return 'application/json; charset=utf-8'

        # from https://github.com/tornadoweb/tornado/pull/1468
        elif mime_type is not None:
            return mime_type
        # if mime_type not detected, use application/octet-stream
        else:
            return "application/octet-stream"


if __name__ == "__main__":
    run()
