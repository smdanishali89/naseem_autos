# -*- coding: utf-8 -*-
{
    'name': "ECUBE General Ledger",

    'summary': """
        Ecube""",
    'author': "Ecube",
    'website': "http://www.ecube.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','account','operating_unit'],

    # always loaded
    'data': [
        'views/templates.xml',
        
    ],

}
