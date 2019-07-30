$(function() {
    function get_parameter_by_name(name) {
        name = name.replace(/[\[]/, "\\[").replace(/[\]]/, "\\]");
        var regex = new RegExp("[\\?&]" + name + "=([^&#]*)"),
            results = regex.exec(location.search);
        return results === null ? "" : decodeURIComponent(results[1].replace(/\+/g, " "));
    }

    var table_list = ['reactions', 'metabolites', 'models', 'genes'],
        all_columns = {reactions: ['bigg_id', 'name', 'model_bigg_id', 'organism'],
                       metabolites: ['bigg_id', 'name', 'model_bigg_id', 'organism'],
                       models: ['bigg_id', 'organism', 'metabolite_count', 'reaction_count', 'gene_count'],
                       genes: ['bigg_id', 'name', 'model_bigg_id', 'organism']},
        all_column_names = {reactions: ['BiGG ID', 'Name', 'Model', 'Organism'],
                            metabolites: ['BiGG ID', 'Name', 'Model', 'Organism'],
                            models: ['BiGG ID', 'Organism', 'Metabolites', 'Reactions', 'Genes'],
                            genes: ['BiGG ID', 'Name', 'Model', 'Organism']};
    for (var i = 0; i < table_list.length; i++) {
        var type = table_list[i],
            selector = '.' + type + '-tablesorter';

        $(selector)
            .tablesorter({
                widthFixed: true,
                sortMultiSortKey: null,
                showProcessing: true
            })
            .tablesorterPager({
                // target the pager
                container: $(selector + ' .pager'),

                // use this format: "http:/mydatabase.com?page={page}&size={size}&{sortList:col}"
                // where {page} is replaced by the page number (or use {page+1} to get a one-based index),
                // {size} is replaced by the number of records to show,
                // {sortList:col} adds the sortList to the url into a "col" array, and {filterList:fcol} adds
                // the filterList to the url into an "fcol" array.
                // So a sortList = [[2,0],[3,0]] becomes "&col[2]=0&col[3]=0" in the url
                // and a filterList = [[2,Blue],[3,13]] becomes "&fcol[2]=Blue&fcol[3]=13" in the url
                ajaxUrl: ('/api/v2' + window.location.pathname +
                          '?query=' + get_parameter_by_name('query') +
                          '&multistrain=' + get_parameter_by_name('multistrain') +
                          '&page={page}&size={size}&{sortList:col}' +
                          '&include_link_urls'),

                // modify the url after all processing has been applied
                customAjaxUrl: function(table, url) {
                    // manipulate the url string as you desire
                    var columns = all_columns[this];
                    url += '&search_type=' + this + '&columns=' + columns.join(',');
                    // trigger my custom event
                    $(table).trigger('changingUrl', url);
                    // send the server the current page
                    return url;
                }.bind(type),

                // add more ajax settings here
                // see http://api.jquery.com/jQuery.ajax/#jQuery-ajax-settings
                ajaxObject: {
                    dataType: 'json'
                },

                ajaxProcessing: function(data) {
                /* Process ajax so that the following information is returned:

                 [ total_rows (number), rows (array of arrays), headers (array; optional) ]
                 example:
                 [
                   100,  // total rows
                   [
                     [ "row1cell1", "row1cell2", ... "row1cellN" ],
                     [ "row2cell1", "row2cell2", ... "row2cellN" ],
                     ...
                     [ "rowNcell1", "rowNcell2", ... "rowNcellN" ]
                   ],
                   [ "header1", "header2", ... "headerN" ] // optional
                 ]
                 OR
                 return [ total_rows, $rows (jQuery object; optional), headers (array; optional) ]

                 */
                    // rows in
                    var results = data.results,
                        // total number of rows (required)
                        total = data.results_count,
                        // columns
                        columns = all_columns[this],
                        column_names = all_column_names[this],
                        // rows out
                        rows = [],
                        r, l, row, this_row, this_val;

                    // check for hiding organism
                    if (HIDE_ORGANISM) {
                        columns = columns.filter(function(x) { return x != 'organism'; });
                        column_names = column_names.filter(function(x) { return x != 'Organism'; });
                    }

                    // rows
                    for (r = 0, l = results.length; r < l; r++) {
                        row = []; // new row array
                        // fill in each column
                        columns.forEach(function(col, i) {
                            this_row = results[r];
                            if (!(col in this_row)) {
                                row.push(null);
                            } else {
                                this_val = this_row[col];
                                // add compartment if present
                                if (col == 'bigg_id' && 'compartment_bigg_id' in this_row)
                                    this_val = this_val + '_' + this_row['compartment_bigg_id'];
                                // make links
                                if ('link_urls' in this_row && col in this_row['link_urls'])
                                    this_val = ('<a href="' + this_row['link_urls'][col] + '">' +
                                                this_val + '</a>');
                                row.push(this_val === null ? '' : this_val);
                            }
                        });
                        // add new row array to rows array
                        rows.push(row);
                    }

                    return [total, rows, column_names];
                }.bind(type),

                // Set this option to false if your table data is preloaded into
                // the table, but you are still using ajax
                processAjaxOnInit: true,

                // output string - default is '{page}/{totalPages}';
                // possible variables: {page}, {totalPages}, {startRow}, {endRow} and {totalRows}
                output: '{startRow} to {endRow} ({totalRows})',

                // apply disabled classname (cssDisabled option) to the pager arrows when the rows
                // are at either extreme is visible; default is true
                updateArrows: true,

                // starting page of the pager (zero based index)
                page: 0,

                // Number of visible rows - default is 10
                size: TABLESORTER_SIZE,

                // Saves the current pager page size and number (requires storage widget)
                savePages: false,

                // Saves tablesorter paging to custom key if defined.
                // Key parameter name used by the $.tablesorter.storage function.
                // Useful if you have multiple tables defined
                // storageKey: 'tablesorter-pager',

                // Reset pager to this page after filtering; set to desired page number (zero-based index),
                // or false to not change page at filter start
                pageReset: false,

                // if true, the table will remain the same height no matter how many records are displayed.
                // The space is made up by an empty table row set to a height to compensate; default is false
                fixedHeight: false,

                // remove rows from the table to speed up the sort of large tables.
                // setting this to false, only hides the non-visible rows; needed if you plan to
                // add/remove rows with the pager e// nabled.
                removeRows: false,

                // If true, child rows will be counted towards the pager set size
                countChildRows: false,

                // css class names of pager arrows
                cssNext        : '.next',  // next page arrow
                cssPrev        : '.prev',  // previous page arrow
                cssFirst       : '.first', // go to first page arrow
                cssLast        : '.last',  // go to last page arrow
                cssGoto        : '.gotoPage', // page select dropdown - select dropdown that set the "page" option

                cssPageDisplay : '.pagedisplay', // location of where the "output" is displayed
                cssPageSize    : '.pagesize', // page size selector - select dropdown that sets the "size" option

                // class added to arrows when at the extremes; see the "updateArrows" option
                // (i.e. prev/first arrows are "disabled" when on the first page)
                cssDisabled    : 'disabled', // Note there is no period "." in front of this class name
                cssErrorRow    : 'tablesorter-errorRow' // error information row

            });
    }
});
