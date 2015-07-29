from os.path import join, isdir, abspath, dirname
from os import mkdir, system
from subprocess import call

import cobra

from ome.base import Session
from ome.models import Model
from ome.dumping.model_dumping import dump_model
from ome import settings

from bigg2.server import static_model_dir as static_dir

if not isdir(static_dir):
    mkdir(static_dir)


def autodetect_model_polisher():
    return abspath(join(dirname(__file__), "..", "bin",
                        "ModelPolisher-0.8.jar"))


def make_all_static_models():
    """write static models for all models in the database"""
    failed_models = []
    polisher_path = autodetect_model_polisher()
    session = Session()
    bigg_ids = [i[0] for i in session.query(Model.bigg_id)]
    for bigg_id in bigg_ids:
        # keep track of which models failed
        if not write_static_model(bigg_id, polisher_path):
            failed_models.append(bigg_id)
    session.close()
    if len(failed_models) > 0:
        return "Failed for models " + " ".join(failed_models)


def write_static_model(bigg_id, model_polisher_path=None):
    """write out static files for a model with the given bigg ID

    This will output compressed and uncompressed SBML L3 + FBCv2, JSON,
    and MAT files"""
    success = True
    model = dump_model(bigg_id)
    raw_sbml_filepath = bigg_id + "_raw.xml"
    sbml_filepath = join(static_dir, bigg_id + ".xml")
    if model_polisher_path is None:
        model_polisher_path = autodetect_model_polisher()
    try:
        cobra.io.write_sbml_model(model, raw_sbml_filepath)
    except Exception as e:
        success = False
        print("Failed to export sbml model '%s': %s" % (bigg_id, e.message))
    else:
        # polish
        command = [settings.java,
                   '-jar',
                   '-Xms8G',
                   '-Xmx8G',
                   '-Xss128M',
                   '-Duser.language=en',
                   model_polisher_path,
                   '--user=%s' % settings.postgres_user,
                   '--passwd=%s' % settings.postgres_password,
                   '--host=%s' % settings.postgres_host,
                   '--dbname=%s' % settings.postgres_database,
                   '--input=%s' % raw_sbml_filepath,
                   '--output=%s' % sbml_filepath,
                   '--compress-output=false',
                   '--omit-generic-terms=false',
                   '--log-level=INFO',
                   '--log-file=model_polisher_%s.log' % bigg_id]
        polish_result = call(command)
        if polish_result == 0:
            # compress model
            system("gzip --keep --force --best " + sbml_filepath)
        else:
            success = False


    cobra.io.save_matlab_model(model, join(static_dir, bigg_id + ".mat"))
    cobra.io.save_json_model(model, join(static_dir, bigg_id + ".json"))
    return success

if __name__ == "__main__":
    import sys
    sys.exit(make_all_static_models())
