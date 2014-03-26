CREATE TABLE public.gene (
	modelversion_id int8,
	locusname varchar(255),
	putativeidentification varchar(255),
	genesymbol varchar(255),
	cellularrole varchar(255),
	fiveprimecoordinate int8,
	threeprimecoordinate int8,
	genelength int4,
	percentgc float8,
	genbankid varchar(255),
	rnatype varchar(1),
	geneindex_id int8,
	isdeleted varchar(1),
	created_by varchar(32),
	last_modified_dt date,
	last_modified_by varchar(32),
	chromosome varchar(255),
	proteinlength int4,
	pi int4,
	strand varchar(1),
	cellularsubrole varchar(255),
	ecnumber varchar(255),
	swissprotentryname varchar(255),
	nucleotidesequence text,
	last_modified_bysystem varchar(1),
	recordversion int4,
	geneindexstrainname varchar(255),
	geneindexsequencingcenter varchar(255),
	geneindexsource varchar(255),
	organismstrain_id int8,
	organismstrainname varchar(255),
	organism_id int8,
	organismgenus varchar(255),
	organismothernames varchar(255),
	associated_proteins varchar(1000),
	associated_reactions varchar(1000),
	exclusion_reason varchar(1000),
	gene_id serial NOT NULL
);

CREATE TABLE public.gpr (
	modelversion_id int8,
	reaction_id int8,
	protein_id int8,
	gene_id int8,
	reactionrule varchar(500)
);

CREATE TABLE public.metabolite (
	modelversion_id int4,
	abbreviation varchar(255),
	officialname varchar(255),
	formula varchar(255),
	charge int4,
	compartment varchar(255),
	notes varchar(2000),
	connectivity int4,
	casnumber varchar(255),
	keggid varchar(1000),
	molecule_id serial NOT NULL
);

create sequence test_index_seq;
create sequence model15_modelid_seq;
CREATE TABLE public.model (
	"index" int4 DEFAULT nextval('test_index_seq'::regclass) NOT NULL,
	description varchar(250),
	currentime timestamp DEFAULT now(),
	modelversion_id int4 DEFAULT nextval('model15_modelid_seq'::regclass) NOT NULL,
	"name" varchar(250),
	firstcreated timestamptz DEFAULT now()
);

create sequence "description _index_seq";
CREATE TABLE public.notes (
	"table" varchar(100),
	description varchar(500),
	"index" int4 DEFAULT nextval('"description _index_seq"'::regclass) NOT NULL
);

CREATE TABLE public.reaction (
	modelversion_id int4,
	officialname varchar(255),
	abbreviation varchar(255),
	direction varchar(255),
	istransformation char(1),
	istranslocation char(1),
	notes varchar(2000),
	discriminator varchar(255),
	isdeleted char(1),
	created_by varchar(32),
	last_modified_dt date,
	last_modified_by varchar(32),
	equation varchar(4000),
	ecnumber varchar(255),
	tcnumber varchar(255),
	equationformula varchar(4000),
	reactionnumber int4,
	subsystem varchar(255),
	proteinclassdescription varchar(1000),
	hasreferences varchar(1000),
	metabolicregion varchar(1000),
	hasnotes varchar(1000),
	modelreactionnotes varchar(1000),
	reaction_id serial NOT NULL,
	gpr varchar(1000),
	lower_bound numeric,
	upper_bound numeric,
	objective_coefficient numeric
);

CREATE TABLE public.reactionmetabolite (
	modelversion_id int8,
	reaction_id int8,
	molecule_id int8,
	compartment varchar(250),
	s numeric
);

CREATE TABLE public.simulation (
	"index" serial NOT NULL,
	modelversion_id int4,
	reactions_added int4,
	reactions_deleted int4,
	results varchar(1000),
	modified timestamp DEFAULT now(),
	created timestamp DEFAULT now(),
	simulation_id serial NOT NULL
);

CREATE TABLE public."transaction" (
	username varchar(250),
	"action" varchar(250),
	"date" timestamp DEFAULT '2013-10-25 12:33:50.91233'::timestamp without time zone,
	modelversion_id int4,
	"index" serial NOT NULL
);

CREATE TABLE public."version" (
	"index" int4,
	moid int4,
	"version" varchar(25),
	firstcreated timestamp,
	modified timestamp
);

CREATE TABLE public.ecocycgenes (
	"unique-id" varchar(2250),
	"blattner-id	" varchar(2250),
	"name" varchar(2250),
	"product-name" varchar(2250),
	"swiss-prot-id" varchar(2250),
	replicon varchar(2250),
	"start-base" varchar(2250),
	"end-base" varchar(2250),
	synonyms1 varchar(2250),
	synonyms2 varchar(2250),
	synonyms3 varchar(2250),
	synonyms4 varchar(2250),
	"gene-class1" varchar(2250),
	"gene-class2" varchar(2250),
	"gene-class3" varchar(2250),
	"gene-class4" varchar(2250)
);

CREATE INDEX geneidindex ON gene USING btree (gene_id)

CREATE INDEX gprgeneindex ON gpr USING btree (gene_id)

CREATE INDEX gprmodelversion ON gpr USING btree (modelversion_id)

CREATE INDEX gprreactionindex ON gpr USING btree (reaction_id)

CREATE INDEX metamoleculeindex ON metabolite USING btree (molecule_id)

CREATE INDEX metmodelversionindex ON metabolite USING btree (modelversion_id)

CREATE INDEX modelidindex ON model USING btree (index)

CREATE INDEX modelversionindex ON gene USING btree (modelversion_id)

CREATE INDEX rmmodelversion ON reactionmetabolite USING btree (modelversion_id)

CREATE INDEX rmmoleculeindex ON reactionmetabolite USING btree (molecule_id)

CREATE INDEX rmodelversionindex ON reaction USING btree (modelversion_id)

CREATE INDEX rmreactionindex ON reactionmetabolite USING btree (reaction_id)

CREATE INDEX rreactionidindex ON reaction USING btree (reaction_id)

CREATE UNIQUE INDEX simulation_pkey ON simulation USING btree (index)
