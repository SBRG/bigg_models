<?xml version="1.0" encoding="UTF-8"?>
<!-- Copyright © 2019 The Regents of the University of California. -->
<!-- Style file for the display of BiGG SBML files in web browsers -->
<!-- Author: Andreas Dräger -->
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:sbml="http://www.sbml.org/sbml/level3/version1/core"
  xmlns:fbc="http://www.sbml.org/sbml/level3/version1/fbc/version2">
  <xsl:output omit-xml-declaration="no" encoding="utf-8"
    indent="yes" />
  <xsl:template match="/sbml:sbml">
    <!-- Define variables -->
    <xsl:variable name="model_id" select="sbml:model/@id" />
    <xsl:variable name="model_name" select="sbml:model/@name" />
    <!-- XHTML content -->
    <html xmlns="http://www.w3.org/1999/xhtml">
      <head>
        <title>
          <xsl:value-of select="$model_id" />
        </title>
        <link rel="stylesheet"
          href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.4/css/bootstrap.min.css" />
        <style>
          body, dl {
            font-size: 14px;
            height: 100%;
            width: 100%;
            color: #444444;
            font-family: Helvetica, sans-serif;
            margin-top: 0px !important;
            margin-left: 0px !important;
            line-height: 1 !important;
          }  
          address {
            font-style: italic;
            line-height: 1 !important;
          }  
          p, dl  {
            margin: 14px 0px 14px !important;
          }  
          dt {
            font-weight: normal;
          }  
          dd {
            margin-left: 25px;
          }  
          h1 {
            font-family: Lato, Helvetica Neue, Helvetica, Arial, sans-serif !important;
            font-weight: 700; color:#EFF8FF;
            text-shadow: 0px 0px 10px rgba(0, 0, 0, 0.5);
            text-decoration-color: -moz-use-text-color;
            margin-bottom: 40px; margin-top: 0px !important;
          }  
          h2 {
            font-weight: bold;
            font-size: 21px;
          }
          table { 
            border-spacing: 10px 4px;
            border-collapse: separate;
          }
        </style>
      </head>
      <body>
        <div style="height: 60px; background-color: #09F;">
          <div style="margin-left: auto; margin-right: auto; width: 970px;">
            <h1>
              <div class="dc:title">
                <xsl:value-of select="$model_id" />
                -
                <xsl:value-of select="$model_name" />
              </div>
            </h1>
            <xsl:copy-of select="//sbml:model/sbml:notes" />
            <h2>Model overview</h2>
            <!-- TODO: create table of contents -->
            <div class="tabbable" style="margin-bottom:50px;">
              <ul class="nav nav-tabs">
                <li>
                  <a href="#tab_units" data-toggle="tab">Units</a>
                </li>
                <li>
                  <a href="#tab_compartments" data-toggle="tab">Compartments</a>
                </li>
                <li class="active">
                  <a href="#tab_metabolites" data-toggle="tab">Metabolites</a>
                </li>
                <li>
                  <a href="#tab_genes" data-toggle="tab">Genes</a>
                </li>
                <li>
                  <a href="#tab_parameters" data-toggle="tab">Parameters</a>
                </li>
                <li>
                  <a href="#tab_reactions" data-toggle="tab">Reactions</a>
                </li>
                <li>
                  <a href="#tab_objectives" data-toggle="tab">Objectives</a>
                </li>
              </ul>
              <div class="tab-content">
                <div class="tab-pane" id="tab_units">
                  <table border="0">
                    <tr>
                      <th align="left">Id</th>
                      <th align="left">Name</th>
                      <th align="left">Definition</th>
                    </tr>
                    <xsl:for-each select="//sbml:unitDefinition">
                      <xsl:sort select="@id"/>
                      <xsl:variable name="unit_id" select="@id"/>
                      <xsl:variable name="unit_name" select="@name"/>
                      <tr>
                        <td><tt><xsl:value-of select="$unit_id"/></tt></td>
                        <td><xsl:value-of select="$unit_name"/></td>
                        <td><xsl:copy-of select="sbml:notes" /></td>
                      </tr>
                    </xsl:for-each>
                  </table>
                </div>
                <div class="tab-pane" id="tab_compartments">
                  <table border="0">
                    <tr>
                      <th align="left">BiGG id</th>
                      <th align="left">Name</th>
                    </tr>
                    <xsl:for-each select="//sbml:compartment">
                      <xsl:sort select="@id" />
                      <xsl:variable name="comp_id" select="@id" />
                      <xsl:variable name="comp_name"
                        select="@name" />
                      <tr>
                        <td>
                          <a
                            href="http://identifiers.org/bigg.compartment/{$comp_id}"
                            target="_blank"
                            title="Access compartment '{$comp_name}' in BiGG knowledgebase.">
                            <tt>
                              <xsl:value-of select="$comp_id" />
                            </tt>
                          </a>
                        </td>
                        <td>
                          <xsl:value-of select="$comp_name" />
                        </td>
                      </tr>
                    </xsl:for-each>
                  </table>
                </div>
                <div class="tab-pane active" id="tab_metabolites">
                  <table border="0">
                    <tr>
                      <th align="left">BiGG id</th>
                      <th align="left">Name</th>
                      <th align="left">Compartment</th>
                    </tr>
                    <xsl:for-each select="//sbml:species">
                      <xsl:sort select="@id" />
                      <tr>
                        <xsl:variable name="species_id"
                          select="@id" />
                        <xsl:variable name="species_name"
                          select="@name" />
                        <xsl:variable name="species_comp"
                          select="@compartment" />
                        <td>
                          <a
                            href="http://identifiers.org/bigg.metabolite/{$species_id}"
                            target="_blank"
                            title="Access metabolite '{$species_name}' in BiGG knowledgebase.">
                            <tt>
                              <xsl:value-of select="@id" />
                            </tt>
                          </a>
                        </td>
                        <td>
                          <xsl:value-of select="$species_name" />
                        </td>
                        <!--<xsl:choose> <xsl:when test="@color"> Do the 
                          Task </xsl:when> <xsl:otherwise> Do the Task </xsl:otherwise> </xsl:choose> -->
                        <!--<td><xsl:value-of select="//sbml:compartment[@id=$species_comp]/@name"/></td> -->
                        <td>
                          <a
                            href="http://identifiers.org/bigg.compartment/{$species_comp}"
                            target="_blank"
                            title="Access compartment '{$species_comp}' in BiGG knowledgebase.">
                            <tt>
                              <xsl:value-of select="$species_comp" />
                            </tt>
                          </a>
                        </td>
                      </tr>
                    </xsl:for-each>
                  </table>
                </div>
                <div class="tab-pane" id="tab_genes">
                  <table border="0">
                    <tr>
                      <th align="left">Label</th>
                      <th align="left">Name</th>
                    </tr>
                    <xsl:for-each select="//fbc:geneProduct">
                      <xsl:sort select="@fbc:label" />
                      <xsl:variable name="gene_label"
                        select="@fbc:label" />
                      <xsl:variable name="gene_name"
                        select="@fbc:name" />
                      <tr>
                        <!-- TODO: conditional statement to find an appropriate 
                          link -->
                        <td><!--<a href=""> -->
                          <xsl:value-of select="$gene_label" /><!--</a> -->
                        </td>
                        <td>
                          <xsl:value-of select="$gene_name" />
                        </td>
                      </tr>
                    </xsl:for-each>
                  </table>
                </div>
                <div class="tab-pane" id="tab_parameters">
                  <table border="0">
                    <tr>
                      <th align="left">Id</th>
                      <th align="left">Name</th>
                      <th align="left">Value</th>
                      <th align="left">Unit</th>
                    </tr>
                    <xsl:apply-templates select="//sbml:parameter" />
                    <xsl:for-each select="//sbml:parameter">
                      <xsl:sort select="@id" />
                      <xsl:variable name="param_id" select="@id" />
                      <xsl:variable name="param_name"
                        select="@name" />
                      <xsl:variable name="param_val"
                        select="@value" />
                      <xsl:variable name="param_unit"
                        select="@units" />
                      <tr>
                        <td>
                          <tt>
                            <xsl:value-of select="$param_id" />
                          </tt>
                        </td>
                        <td>
                          <xsl:value-of select="$param_name" />
                        </td>
                        <td>
                          <xsl:value-of select="$param_val" />
                        </td>
                        <td>
                          <xsl:value-of select="$param_unit" />
                        </td>
                      </tr>
                    </xsl:for-each>
                  </table>
                </div>
                <div class="tab-pane" id="tab_reactions">
                  <table border="0">
                    <tr>
                      <th align="left">BiGG id</th>
                      <th align="left">Name</th>
                    </tr>
                    <xsl:for-each select="//sbml:reaction">
                      <xsl:sort select="@id" />
                      <xsl:variable name="react_id" select="@id" />
                      <xsl:variable name="react_name"
                        select="@name" />
                      <tr>
                        <td>
                          <a
                            href="http://identifiers.org/bigg.reaction/{$react_id}"
                            target="_blank"
                            title="Access reaction '{$react_name}' in BiGG knowledgebase.">
                            <tt>
                              <xsl:value-of select="$react_id" />
                            </tt>
                          </a>
                        </td>
                        <td>
                          <xsl:value-of select="$react_name" />
                        </td>
                      </tr>
                    </xsl:for-each>
                  </table>
                </div>
                <div class="tab-pane" id="tab_objectives">
                  <h3>Objective function</h3>
                  <!-- TODO: objective function -->
                </div>
              </div>
            </div>
          </div>
        </div>
        <script
          src="https://ajax.googleapis.com/ajax/libs/jquery/2.1.3/jquery.min.js" />
        <script
          src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.4/js/bootstrap.min.js" />
      </body>
    </html>
  </xsl:template>
</xsl:stylesheet>