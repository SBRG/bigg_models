from ome import settings
from ome.loading.model_loading import parse
from server import directory
from os.path import join
import os
import cobra
import shutil

model_dir = join(settings.data_directory, 'models')

dirs = os.listdir(model_dir)
for model_file in dirs:
	#model, old_ids = parse.load_and_normalize(join(model_dir,  model_file))
	try:
		model = cobra.io.read_sbml_model(join(model_dir, model_file))
		bigg_id = model.id
		format = 'xml'
		#target_dir = join(root_directory, 'static', 'published_models', '%s_published.%s' % (bigg_id, format)
		target_dir = join(directory, 'static', 'published_models')

		# load using cobrapy (as sbml or mat)
		# grab the bigg_id (model.id)
		if not os.path.exists(target_dir):
			os.makedirs(target_dir)
			shutil.copy(join(model_dir, model_file), join(target_dir,'%s_published.%s' % (bigg_id, format)))
		else:
			shutil.copy(join(model_dir, model_file), join(target_dir,'%s_published.%s' % (bigg_id, format)))
		#os.rename(join(target_dir, model_file), '%s_published.%s' % (bigg_id, format) )
	except:
		print "%s is not valid file" % model_file