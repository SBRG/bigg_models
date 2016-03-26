CREATE OR REPLACE FUNCTION create_index(table_name text, column_name text)
RETURNS void
AS
$$ 
declare 
   l_count integer;
   index_name text := table_name || '_' || column_name;
begin
  select count(*)
     into l_count
  from pg_indexes
  where schemaname = 'public'
    and tablename = lower(table_name)
    and indexname = lower(index_name);

  if l_count = 0 then 
     raise notice 'Creating index %', index_name;
     execute 'create index ' || index_name || ' on ' || table_name || ' using gin (' || column_name || ' gin_trgm_ops);';
  else
     raise notice 'Index % already exists', index_name;
  end if;
end;
$$ LANGUAGE plpgsql;

-- load the extension
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- load the indices
SELECT create_index('reaction', 'bigg_id');
SELECT create_index('reaction', 'name');
SELECT create_index('component', 'bigg_id');
SELECT create_index('component', 'name');
SELECT create_index('genome_region', 'bigg_id');
SELECT create_index('gene', 'name');
SELECT create_index('model', 'bigg_id');
SELECT create_index('genome', 'organism');
