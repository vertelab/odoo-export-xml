# -*- coding: utf-8 -*-
##############################################################################
#
# OpenERP, Open Source Management Solution, third party addon
# Copyright (C) 2004-2015 Vertel AB (<http://vertel.se>).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

try:
    import json
except ImportError:
    import simplejson as json

import openerp.http as http
from openerp.http import request
from openerp.addons.web.controllers.main import ExcelExport


from fnmatch import fnmatch,fnmatchcase
from lxml import etree


import logging
_logger = logging.getLogger(__name__)


def export_xml(lines):
    document = etree.Element('openerp')
    data = etree.SubElement(document,'data')
    for line in lines:
        if line.id:
            k,id = line.get_external_id().items()[0] if line.get_external_id() else 0,"%s-%s" % (line._name,line.id)
            _logger.info("Reporting Block id = %s" % id)          
            record = etree.SubElement(data,'record',id=id,model=line._name)
            names = [name for name in line.fields_get().keys() if fnmatch(name,'in_group*')] + [name for name in line.fields_get().keys() if fnmatch(name,'sel_groups*')]
            for field,values in line.fields_get().items():
                if not field in ['create_date','nessage_ids','id','write_date','create_uid','__last_update','write_uid',] + names:
                    if values.get('type') in ['boolean','char','text','float','integer','selection','date','datetime']:
                        if eval('line.%s' % field):
                            etree.SubElement(record,'field',name = field).text = "%s" % eval('line.%s' % field)
                    elif values.get('type') in ['many2one']:
                        if eval('line.%s' % field):                                     
                            k,id = eval('line.%s.get_external_id().items()[0]' % field) if eval('line.%s.get_external_id()' % field) else (0,"%s-%s" % (eval('line.%s._name' % field),eval('line.%s.id' % field)))
                            if id == "":
                                id = "%s-%s" % (eval('line.%s._name' % field),eval('line.%s.id' % field))
                            etree.SubElement(record,'field',name=field,ref="%s" % id)
                    elif values.get('type') in ['one2many']:  # Update from the other end
                        pass
                    elif values.get('type') in ['many2many']: # TODO
                        _logger.info("M2M = %s, %s" % (field,value)) 
                         #~ if eval('line.%s' % field):                                     
                            #~ k,id = eval('line.%s.get_external_id().items()[0]' % field) if eval('line.%s.get_external_id()' % field) else (0,"%s-%s" % (eval('line.%s._name' % field),eval('line.%s.id' % field)))
                            #~ if id == "":
                                #~ id = "%s-%s" % (eval('line.%s._name' % field),eval('line.%s.id' % field))
                            #~ etree.SubElement(record,'field',name=field,ref="%s" % id)
                        #~ 
                        #~ etree.SubElement(record,'field',name=field,ref="%s %s" % (values.get('type'),eval('line.%s' % field)))
                        
    
    return document

def get_related(models,depth):
    objects = set()
    if depth < 4:
        for model in models:
            _logger.info('Get related model %s id %s' % (model._name,model.id))
            for field,values in model.fields_get().items(): 
                if not field in ['create_date','nessage_ids','id','write_date','create_uid','__last_update','write_uid']:
                    if values.get('type') in ['many2one']:
                        for related in get_related(eval("model.%s" % field),depth+1):
                            objects.add(related)
            objects.add(model)
    return list(objects)


class XMLExport(http.Controller):




    @http.route('/web/export/xml', type='http', auth='user')
    def export_xls_view(self, data, token):
        
        _logger.info("XMLEport data %s " % (data)) 

        data = json.loads(data)
        model = data.get('model', [])
        rows = data.get('rows', [])
    
        _logger.info("XMLEport model %s rows %s" % (model,rows)) 

        document = etree.tostring(export_xml(get_related(request.registry[model].browse(request.cr,request.uid,rows),0)),pretty_print=True,encoding="utf-8")
        
        return request.make_response(
            document,
            headers=[
                ('Content-Disposition', 'attachment; filename="%s.xml"'
                 % model),
                ('Content-Type', 'application/rdf+xml'),
                ('Content-Length', len(document)),
            ]
        )
        
        
    @http.route('/web/export/<model("ir.model"):model>/<int:res_id>/xml', type='http', auth='public')
    def export_xls_view(self, model=False, res_id=None):     
        document = etree.tostring(export_xml(get_related(request.registry[model.model].browse(request.cr,request.uid,res_id),0)),pretty_print=True,encoding="utf-8")
        return request.make_response(
            document,
            headers=[
                ('Content-Disposition', 'attachment; filename="%s.xml"' % model.model),
                ('Content-Type', 'application/rdf+xml'),
                ('Content-Length', len(document)),
            ]
        )
