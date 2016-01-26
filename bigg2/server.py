#!/usr/bin/env python
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
from os.path import abspath, dirname, join
from jinja2 import Environment, PackageLoader
from sqlalchemy.orm import sessionmaker, aliased, Bundle
from sqlalchemy import create_engine, desc, func, or_
from collections import Counter
import simplejson as json
import subprocess
import os
from os.path import isfile
import mimetypes
import datetime

from six import iteritems

from bigg2 import queries
from bigg2.queries import NotFoundError
import ome
from ome import settings
from ome.models import (Model, Component, Reaction, Compartment, Metabolite,
                        CompartmentalizedComponent, ModelReaction,
                        ReactionMatrix, GeneReactionMatrix,
                        ModelCompartmentalizedComponent, ModelGene, Gene,
                        Comments, GenomeRegion, Genome)
from ome.base import Session
from ome.loading.parse import split_compartment


# sbml validator
try:
    import cobra_sbml_validator
except ImportError:
    print('COBRA SBML Validator not installed')
    HAS_SBML_VALIDATOR = False
else:
    HAS_SBML_VALIDATOR = True


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
    routes = [
        (r'/', MainHandler),
        #
        # Universal
        #
        (r'/api/%s/(?:models/)?universal/reactions/?$' % api_v, UniversalReactionListHandler),
        (r'/(?:models/)?universal/reactions/?$', UniversalReactionListDisplayHandler),
        #
        (r'/api/%s/(?:models/)?universal/reactions/([^/]+)/?$' % api_v, UniversalReactionHandler),
        (r'/(?:models/)?universal/reactions/([^/]+)/?$', UniversalReactionHandler),
        #
        (r'/api/%s/(?:models/)?universal/metabolites/?$' % api_v, UniversalMetaboliteListHandler),
        (r'/(?:models/)?universal/metabolites/?$', UniversalMetaboliteListDisplayHandler),
        #
        (r'/api/%s/(?:models/)?universal/metabolites/([^/]+)/?$' % api_v, UniversalMetaboliteHandler),
        (r'/(?:models/)?universal/metabolites/([^/]+)/?$', UniversalMetaboliteHandler),
        #
        (r'/api/%s/compartments/?$' % api_v, CompartmentListHandler),
        (r'/compartments/?$', CompartmentListHandler),
        #
        (r'/api/%s/compartments/([^/]+)/?$' % api_v, CompartmentHandler),
        (r'/compartments/([^/]+)/?$', CompartmentHandler),
        #
        (r'/api/%s/genomes/?$' % api_v, GenomeListHandler),
        (r'/genomes/?$', GenomeListDisplayHandler),
        #
        (r'/api/%s/genomes/([^/]+)/?$' % api_v, GenomeHandler),
        (r'/genomes/([^/]+)/?$', GenomeHandler),
        #
        # By model
        #
        (r'/api/%s/models/?$' % api_v, ModelListHandler),
        (r'/models/?$', ModelsListDisplayHandler),
        #
        (r'/api/%s/models/([^/]+)/?$' % api_v, ModelHandler),
        (r'/models/([^/]+)/?$', ModelHandler),
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
        (r'/models/([^/]+)/metabolites/([^/]+)/?$', MetaboliteHandler),
        #
        (r'/api/%s/models/([^/]+)/genes/([^/]+)/?$' % api_v, GeneHandler),
        (r'/models/([^/]+)/genes/([^/]+)/?$', GeneHandler),
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
        # Version
        (r'/api/%s/database_version$' % api_v, APIVersionHandler),
        #
        # Static/Download
        (r'/static/(.*)$', StaticFileHandlerWithEncoding, {'path': join(directory, 'static')}),
        #
        # redirects
        (r'/multiecoli/?$', RedirectHandler, {'url': 'http://bigg1.ucsd.edu/multiecoli'})
    ]

    # SBML validator
    if HAS_SBML_VALIDATOR:
        routes += [
            (r'/validator/?$', RedirectHandler, {'url': '/validator/app'}),
            (r'/sbml_validator/?$', RedirectHandler, {'url': '/validator/app'}),
            (r'/validator/app$', cobra_sbml_validator.ValidatorFormHandler),
            (r'/validator/upload$', cobra_sbml_validator.Upload)
        ]

    return tornado.web.Application(routes, debug=debug)


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
    except ValueError as e:
        raise HTTPError(status_code=400, reason=e.message)
    finally:
        session.close()


class BaseHandler(RequestHandler):
    def write(self, value):
        # note that serving a json list is a security risk
        # This is meant to be serving public-read only data only.
        if isinstance(value, (dict, list, tuple)):
            value_str = json.dumps(value)
            RequestHandler.write(self, value_str)
            self.set_header('Content-type', 'application/json; charset=utf-8')
        else:
            RequestHandler.write(self, value)

    def return_result(self, result):
        """Returns result as either rendered HTML or JSON

        This is suitable for cases where the template takes exactly the same
        result as the JSON api. This function will serve JSON if the request
        URI starts with JSON, otherwise it will render the objects template
        with the data"""
        if self.request.uri.startswith("/api"):
            self.write(result)
        else:
            self.write(self.template.render(result))
        self.finish()


class PageableHandler(BaseHandler):
    """HTTP requests can pass in arguments for page, size, columns, and the
    sort_column.

    TODO test this class.

    """

    def _get_pager_args(self, default_sort_column=None, sort_direction="ascending"):
        query_kwargs = {
            "page": self.get_argument('page', None),
            "size": self.get_argument('size', None),
            "sort_column": default_sort_column,
            "sort_direction": sort_direction
        }

        # determine the columns
        column_str = self.get_argument("columns", None)
        columns = column_str.split(",") if column_str else []

        # determine which column we are sorting by
        # These are parameters formatted as col[i] = 0 (or 1 for descending)
        for param_name, param_value in iteritems(self.request.query_arguments):
            if not (param_name.startswith("col[") and
                    param_name.endswith("]")):
                continue
            try:
                # get the number in col[?]
                col_index = int(param_name[4:-1])
                sort_direction = "ascending" if param_value[0] == "0" \
                    else "descending"
            except ValueError as e:
                raise HTTPError(status_code=400,
                                reason="could not parse %s=%s" %
                                (param_name, param_value))
            # convert these integers into meaningful sort params
            try:
                query_kwargs["sort_column"] = columns[col_index]
            except IndexError:
                raise HTTPError(status_code=400,
                                reason="column #%d not found in columns" %
                                col_index)
            else:
                query_kwargs["sort_direction"] = sort_direction

        return query_kwargs


class MainHandler(BaseHandler):
    def get(self):
        template = env.get_template('index.html')
        self.write(template.render())
        self.finish()


# reactions
class UniversalReactionListHandler(PageableHandler):
    def get(self):
        kwargs = self._get_pager_args(default_sort_column="bigg_id")

        # run the queries
        raw_results = safe_query(queries.get_universal_reactions, **kwargs)

        if "include_link_urls" in self.request.query_arguments:
            raw_results = [dict(x, link_urls={'bigg_id': '/universal/reactions/{bigg_id}'.format(**x)})
                           for x in raw_results]
        result = {'results': [dict(x, model_bigg_id='Universal') for x in raw_results],
                  'results_count': safe_query(queries.get_universal_reactions_count)}

        self.write(result)
        self.finish()


class UniversalReactionListDisplayHandler(BaseHandler):
    def get(self):
        template = env.get_template("list_display.html")
        dictionary = {'results': {'reactions': 'ajax'},
                      'hide_organism': True}
        self.write(template.render(dictionary))
        self.finish()


class UniversalReactionHandler(BaseHandler):
    template = env.get_template("universal_reaction.html")

    def get(self, reaction_bigg_id):
        result = safe_query(queries.get_reaction_and_models, reaction_bigg_id)
        self.return_result(result)


class UniversalMetaboliteListHandler(PageableHandler):
    def get(self):
        # get arguments
        kwargs = self._get_pager_args(default_sort_column="bigg_id")

        raw_results = safe_query(queries.get_universal_metabolites, **kwargs)

        # add links and universal
        if "include_link_urls" in self.request.query_arguments:
            raw_results = [dict(x, link_urls={'bigg_id': '/universal/metabolites/{bigg_id}'.format(**x)})
                           for x in raw_results]
        result = {'results': [dict(x, model_bigg_id='Universal') for x in raw_results],
                  'results_count': safe_query(queries.get_universal_metabolites_count)}

        self.write(result)
        self.finish()


class UniversalMetaboliteListDisplayHandler(BaseHandler):
    def get(self):
        template = env.get_template("list_display.html")
        template_data = {'results': {'metabolites': 'ajax'},
                         'hide_organism': True}
        self.write(template.render(template_data))
        self.finish()


class UniversalMetaboliteHandler(BaseHandler):
    template = env.get_template("universal_metabolite.html")

    def get(self, met_bigg_id):
        results = safe_query(queries.get_metabolite, met_bigg_id)
        self.return_result(results)


class ReactionListHandler(PageableHandler):
    def get(self, model_bigg_id):
        kwargs = self._get_pager_args(default_sort_column="bigg_id")

        raw_results = safe_query(queries.get_model_reactions, model_bigg_id,
                                 **kwargs)
        # add the URL
        if "include_link_urls" in self.request.query_arguments:
            raw_results = [dict(x, link_urls={'bigg_id': '/models/{model_bigg_id}/reactions/{bigg_id}'.format(**x)})
                           for x in raw_results]
        result = {'results': raw_results,
                  'results_count':
                  safe_query(queries.get_model_reactions_count, model_bigg_id)}

        self.write(result)
        self.finish()


class ReactionListDisplayHandler(BaseHandler):
    def get(self, model_bigg_id):
        template = env.get_template("list_display.html")
        template_data = {'results': {'reactions': 'ajax'}}
        self.write(template.render(template_data))
        self.finish()


class ReactionHandler(BaseHandler):
    def get(self, model_bigg_id, reaction_bigg_id):
        results = safe_query(queries.get_model_reaction,
                             model_bigg_id, reaction_bigg_id)
        self.write(results)
        self.finish()


class ReactionDisplayHandler(BaseHandler):
    def get(self, model_bigg_id, reaction_bigg_id):
        template = env.get_template("reaction.html")
        data = safe_query(queries.get_model_reaction,
                             model_bigg_id, reaction_bigg_id)
        for result in data['results']:
            result['reaction_string'] = queries.build_reaction_string(data['metabolites'],
                                                                      result['lower_bound'],
                                                                      result['upper_bound'],
                                                                      False)
        self.write(template.render(data))
        self.finish()


# Compartments
class CompartmentListHandler(BaseHandler):
    template = env.get_template("compartments.html")

    def get(self):
        session = Session()
        results = [{'bigg_id': x[0], 'name': x[1]}
                   for x in session.query(Compartment.bigg_id, Compartment.name)]
        session.close()
        self.return_result(results)


class CompartmentHandler(BaseHandler):
    template = env.get_template("compartment.html")
    
    def get(self, compartment_bigg_id):
        session = Session()
        result_db = (session
                     .query(Compartment)
                     .filter(Compartment.bigg_id == compartment_bigg_id)
                     .first())
        session.close()

        result = {'bigg_id': result_db.bigg_id, 'name': result_db.name}
        self.return_result(result)


# Genomes
class GenomeListHandler(BaseHandler):
    def get(self):
        results = safe_query(queries.get_genome_list)
        self.write(results)
        self.finish()


class GenomeListDisplayHandler(BaseHandler):
    def get(self):
        template = env.get_template("genomes.html")
        results = safe_query(queries.get_genome_list)
        self.write(template.render({'genomes': results}))
        self.finish()


class GenomeHandler(BaseHandler):
    template = env.get_template("genome.html")

    def get(self, genome_ref_string):
        result = safe_query(queries.get_genome_and_models, genome_ref_string)
        self.return_result(result)


# Models
class ModelListHandler(PageableHandler):
    def get(self):
        kwargs = self._get_pager_args(default_sort_column="bigg_id")

        # run the queries
        raw_results = safe_query(queries.get_models, **kwargs)
        if "include_link_urls" in self.request.query_arguments:
            raw_results = [dict(x, link_urls={'bigg_id': '/models/{bigg_id}'.format(**x),
                                              'metabolite_count': '/models/{bigg_id}/metabolites'.format(**x),
                                              'reaction_count': '/models/{bigg_id}/reactions'.format(**x),
                                              'gene_count': '/models/{bigg_id}/genes'.format(**x)})
                           for x in raw_results]
        result = {'results': raw_results,
                  'results_count': safe_query(queries.get_models_count)}

        self.write(result)
        self.finish()


class ModelsListDisplayHandler(BaseHandler):
    def get(self):
        template = env.get_template("list_display.html")
        template_data = {'results': {'models': 'ajax'}}
        self.write(template.render(template_data))
        self.finish()


class ModelDownloadHandler(BaseHandler):
    def get(self, model_bigg_id):
        extension = self.get_argument("format", "json")
        self.redirect("/static/models/%s.%s" % (model_bigg_id, extension))


class ModelHandler(BaseHandler):
    template = env.get_template("model.html")

    def get(self, model_bigg_id):
        result = safe_query(queries.get_model_and_counts, model_bigg_id,
                            static_model_dir=static_model_dir)
        self.return_result(result)


class MetaboliteListHandler(PageableHandler):
    def get(self, model_bigg_id):
        kwargs = self._get_pager_args(default_sort_column="bigg_id")

        # run the queries
        raw_results = safe_query(queries.get_model_metabolites, model_bigg_id,
                                 **kwargs)
        # add the URL
        if "include_link_urls" in self.request.query_arguments:
            raw_results = [dict(x, link_urls={'bigg_id': '/models/{model_bigg_id}/metabolites/{bigg_id}_{compartment_bigg_id}'.format(**x)})
                           for x in raw_results]
        result = {'results': raw_results,
                  'results_count': safe_query(queries.get_model_metabolites_count, model_bigg_id)}

        self.write(result)
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
        self.finish()


class MetaboliteHandler(BaseHandler):
    template = env.get_template("metabolite.html")

    def get(self, model_bigg_id, comp_met_id):
        met_bigg_id, compartment_bigg_id = split_compartment(comp_met_id)
        results = safe_query(queries.get_model_comp_metabolite,
                             met_bigg_id, compartment_bigg_id, model_bigg_id)
        self.return_result(results)


class GeneListHandler(PageableHandler):
    def get(self, model_bigg_id):
        kwargs = self._get_pager_args(default_sort_column="bigg_id")

        raw_results = safe_query(queries.get_model_genes, model_bigg_id,
                                 **kwargs)

        # add the URL
        if "include_link_urls" in self.request.query_arguments:
            raw_results = [dict(x, link_urls={'bigg_id': '/models/{model_bigg_id}/genes/{bigg_id}'.format(**x)})
                           for x in raw_results]
        result = {'results': raw_results,
                  'results_count': safe_query(queries.get_model_genes_count, model_bigg_id)}
        self.write(result)
        self.finish()


class GeneListDisplayHandler(BaseHandler):
    def get(self, model_bigg_id):
        template = env.get_template("list_display.html")
        template_data = {'results': {'genes': 'ajax'}}

        self.write(template.render(template_data))
        self.finish()


class GeneHandler(BaseHandler):
    template = env.get_template("gene.html")

    def get(self, model_bigg_id, gene_bigg_id):
        result = safe_query(queries.get_model_gene,
                            gene_bigg_id, model_bigg_id)
        self.return_result(result)


class SearchHandler(BaseHandler):
    def get(self):
        # get arguments
        query_string = self.get_argument("query")
        page = self.get_argument('page', None)
        size = self.get_argument('size', None)
        search_type = self.get_argument('search_type', None)
        include_link_urls = "include_link_urls" in self.request.query_arguments

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
        self.write(result)
        self.finish()


class SearchDisplayHandler(BaseHandler):
    def get(self):
        template = env.get_template("list_display.html")
        template_data = {'results': {'models': 'ajax',
                                     'reactions': 'ajax',
                                     'metabolites': 'ajax',
                                     'genes': 'ajax'},
                         'tablesorter_size': 20}
        self.write(template.render(template_data))
        self.finish()


class AdvancedSearchHandler(BaseHandler):
    def get(self):
        template = env.get_template('advanced_search.html')
        model_list = safe_query(queries.get_model_list)
        database_sources = safe_query(queries.get_database_sources)

        self.write(template.render({'models': model_list,
                                    'database_sources': database_sources}))
        self.finish()


class AdvancedSearchExternalIDHandler(BaseHandler):
    def post(self):
        query_string = self.get_argument('query', '')
        database_source = self.get_argument('database_source', '')
        session = Session()
        metabolites = queries.get_metabolites_for_database_id(session,
                                                              query_string,
                                                              database_source)
        reactions = queries.get_reactions_for_database_id(session,
                                                          query_string,
                                                          database_source)
        genes = queries.get_genes_for_database_id(session,
                                                  query_string,
                                                  database_source)
        session.close()
        dictionary = {'results': {'metabolites': metabolites,
                                  'reactions': reactions,
                                  'genes': genes},
                      'no_pager': True,
                      'hide_organism': True}

        template = env.get_template("list_display.html")
        self.write(template.render(dictionary))
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
        self.finish()


class AutocompleteHandler(BaseHandler):
    def get(self):
        query_string = self.get_argument("query")

        # get the session
        result_array = safe_query(queries.search_ids_fast, query_string, limit=15)
        self.write(result_array)
        self.finish()


class EscherMapJSONHandler(BaseHandler):
    def get(self, map_name):
        map_json = safe_query(queries.json_for_map, map_name)

        self.write(map_json)
        # need to do this because map_json is a string
        self.set_header('Content-type', 'application/json; charset=utf-8')
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
        self.finish()


class LicenseHandler(BaseHandler):
    def get(self):
        template = env.get_template('about_license_page.html')
        self.write(template.render())
        self.finish()


class APIVersionHandler(BaseHandler):
    def get(self):
        result = safe_query(queries.database_version)
        self.write(result)
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
