from os.path import join, isdir
from os import mkdir, system

import cobra

from ome.base import Session
from ome.models import Model
from ome.dumping.model_dumping import dump_model

from bigg2.server import static_model_dir as static_dir

if not isdir(static_dir):
    mkdir(static_dir)


def make_all_static_models():
    """write static models for all models in the database"""
    failed_models = []
    session = Session()
    bigg_ids = [i[0] for i in session.query(Model.bigg_id)]
    for bigg_id in bigg_ids:
        # keep track of which models failed
        if not write_static_model(bigg_id):
            failed_models.append(bigg_id)
    session.close()
    if len(failed_models) > 0:
        return "Failed for models " + " ".join(failed_models)


def write_static_model(bigg_id):
    """write out static files for a model with the given bigg ID

    This will output compressed and uncompressed SBML L3 + FBCv2, JSON,
    and MAT files"""
    success = True
    model = dump_model(bigg_id)
    sbml_filepath = join(static_dir, bigg_id + ".xml")
    try:
        cobra.io.write_sbml_model(model, sbml_filepath)
    except Exception as e:
        success = False
        print("Failed to export sbml model '%s': %s" % (bigg_id, e.message))
    else:
        # TODO polish

        # compress model
        system("gzip --keep --force --best " + sbml_filepath)

    cobra.io.save_matlab_model(model, join(static_dir, bigg_id + ".mat"))
    cobra.io.save_json_model(model, join(static_dir, bigg_id + ".json"))
    return success

if __name__ == "__main__":
    import sys
    sys.exit(make_all_static_models())
