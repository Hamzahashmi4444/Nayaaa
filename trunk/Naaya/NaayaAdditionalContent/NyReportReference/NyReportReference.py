# The contents of this file are subject to the Mozilla Public
# License Version 1.1 (the "License"); you may not use this file
# except in compliance with the License. You may obtain a copy of
# the License at http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS
# IS" basis, WITHOUT WARRANTY OF ANY KIND, either express or
# implied. See the License for the specific language governing
# rights and limitations under the License.
#
# The Initial Owner of the Original Code is European Environment
# Agency (EEA).  Portions created by Finsiel Romania are
# Copyright (C) European Environment Agency.  All
# Rights Reserved.
#
# Authors:
#
# Alex Ghica, Finsiel Romania

#Python imports
import os
import sys
from copy import deepcopy

#Zope imports
from Globals                                    import InitializeClass
from App.ImageFile import ImageFile
from AccessControl                              import ClassSecurityInfo
from AccessControl.Permissions                  import view_management_screens, view
from Products.PageTemplates.PageTemplateFile    import PageTemplateFile
import Products

#Product imports
from Products.NaayaContent.constants    import *
from Products.NaayaBase.constants       import *
from Products.NaayaBase.NyContainer     import NyContainer
from Products.NaayaBase.NyAttributes    import NyAttributes
from Products.NaayaBase.NyCheckControl  import NyCheckControl
from Products.NaayaBase.NyValidation import NyValidation
from reportreference_item               import reportreference_item

#module constants
METATYPE_OBJECT = 'Naaya Report Reference'
LABEL_OBJECT = 'Report Reference'
PERMISSION_ADD_OBJECT = 'Naaya - Add Naaya Report Reference objects'
OBJECT_FORMS = ['reportreference_add', 'reportreference_edit', 'reportreference_index']
OBJECT_CONSTRUCTORS = ['manage_addNyReportReference_html', 'reportreference_add_html', 'addNyReportReference', 'importNyReportReference']
OBJECT_ADD_FORM = 'reportreference_add_html'
DESCRIPTION_OBJECT = 'This is Naaya Report Reference type.'
PREFIX_OBJECT = 'ref'
PROPERTIES_OBJECT = {
    'id':                           (0, '', ''),
    'title':                        (0, '', ''),
    'description':                  (0, '', ''),
    'coverage':                     (0, '', ''),
    'keywords':                     (0, '', ''),
    'sortorder':                    (0, MUST_BE_POSITIV_INT, 'The Sort order field must contain a positive integer.'),
    'releasedate':                  (0, MUST_BE_DATETIME, 'The Release date field must contain a valid date.'),
    'discussion':                   (0, '', ''),
    'lang':                         (0, '', ''),
    'reference':                    (0, '', '')
}

# this dictionary is updated at the end of the module
config = {
        'product': 'NaayaContent',
        'module': 'NyReportReference',
        'package_path': os.path.abspath(os.path.dirname(__file__)),
        'meta_type': 'Naaya Report Reference',
        'label': 'Report Reference',
        'permission': 'Naaya - Add Naaya Report Reference objects',
        'forms': ['reportreference_add', 'reportreference_edit', 'reportreference_index'],
        'add_form': 'reportreference_add_html',
        'description': 'This is Naaya Report Reference type.',
        'properties': PROPERTIES_OBJECT,
        'default_schema': None,
        'schema_name': '',
        'import_string': 'importNyReportReference',
        '_module': sys.modules[__name__],
        'additional_style': None,
        'icon': os.path.join(os.path.dirname(__file__), 'www', 'NyReportReference.gif'),
        '_misc': {
                'NyReportReference.gif': ImageFile('www/NyReportReference.gif', globals()),
                'NyReportReference_marked.gif': ImageFile('www/NyReportReference_marked.gif', globals()),
            },
    }

def reportreference_add_html(self, REQUEST=None, RESPONSE=None):
    """ """
    return self.getFormsTool().getContent({'here': self, 'kind': METATYPE_OBJECT, 'action': 'addNyReportReference'}, 'reportreference_add')

def addNyReportReference(self, id='', title='', description='', coverage='', keywords='',
    sortorder='', contributor=None, releasedate='', discussion='', lang=None, reference='', REQUEST=None, **kwargs):
    """
    Create a Report Reference type of object.
    """
    #process parameters
    id = self.utCleanupId(id)
    if not id: id = self.generateItemId(PREFIX_OBJECT)
    try: sortorder = abs(int(sortorder))
    except: sortorder = DEFAULT_SORTORDER
    #check mandatory fiels
    l_referer = ''
    if REQUEST is not None: l_referer = REQUEST['HTTP_REFERER'].split('/')[-1]
    if not(l_referer == 'manage_addNyReportReference_html' or l_referer.find('manage_addNyReportReference_html') != -1) and REQUEST:
        r = self.getSite().check_pluggable_item_properties(METATYPE_OBJECT, id=id, title=title, \
            description=description, coverage=coverage, keywords=keywords, sortorder=sortorder, \
            releasedate=releasedate, discussion=discussion, reference=reference)
    else:
        r = []
    if not len(r):
        #process parameters
        if contributor is None: contributor = self.REQUEST.AUTHENTICATED_USER.getUserName()
        if self.glCheckPermissionPublishObjects():
            approved, approved_by = 1, self.REQUEST.AUTHENTICATED_USER.getUserName()
        else:
            approved, approved_by = 0, None
        releasedate = self.process_releasedate(releasedate)
        if lang is None: lang = self.gl_get_selected_language()

        #generate cross-reference links
        ref_links = {'en':[]}
        if lang == 'en':
            ref_links['en'].extend(self.getReferenceData(reference))

        #create object
        ob = NyReportReference(id, reference, description, coverage, keywords, sortorder, contributor, releasedate, lang, reference, ref_links)
        self.gl_add_languages(ob)
        ob.createDynamicProperties(self.processDynamicProperties(METATYPE_OBJECT, REQUEST, kwargs), lang)
        self._setObject(id, ob)
        #extra settings
        ob = self._getOb(id)
        ob.updatePropertiesFromGlossary(lang)
        ob.approveThis(approved, approved_by)
        ob.submitThis()
        if discussion: ob.open_for_comments()
        self.recatalogNyObject(ob)
        self.notifyFolderMaintainer(self, ob)
        #redirect if case
        if REQUEST is not None:
            if l_referer == 'manage_addNyReportReference_html' or l_referer.find('manage_addNyReportReference_html') != -1:
                return self.manage_main(self, REQUEST, update_menu=1)
            elif l_referer == 'reportreference_add_html':
                self.setSession('referer', self.absolute_url())
                REQUEST.RESPONSE.redirect('%s/messages_html' % self.absolute_url())
    else:
        if REQUEST is not None:
            self.setSessionErrors(r)
            self.set_pluggable_item_session(METATYPE_OBJECT, id=id, title=title, \
                description=description, coverage=coverage, keywords=keywords, \
                sortorder=sortorder, releasedate=releasedate, discussion=discussion, lang=lang, reference=reference)
            REQUEST.RESPONSE.redirect('%s/reportreference_add_html' % self.absolute_url())
        else:
            raise Exception, '%s' % ', '.join(r)

def importNyReportReference(self, param, id, attrs, content, properties, discussion, objects):
    pass
    #TODO: to be added
#    #this method is called during the import process
#    try: param = abs(int(param))
#    except: param = 0
#    if param == 3:
#        #just try to delete the object
#        try: self.manage_delObjects([id])
#        except: pass
#    else:
#        ob = self._getOb(id, None)
#        if param in [0, 1] or (param==2 and ob is None):
#            if param == 1:
#                #delete the object if exists
#                try: self.manage_delObjects([id])
#                except: pass
#            addNyReportReference(self, id=id,
#                sortorder=attrs['sortorder'].encode('utf-8'),
#                contributor=self.utEmptyToNone(attrs['contributor'].encode('utf-8')),
#                discussion=abs(int(attrs['discussion'].encode('utf-8'))))
#            ob = self._getOb(id)
#            for property, langs in properties.items():
#                for lang in langs:
#                    ob._setLocalPropValue(property, lang, langs[lang])
#            ob.approveThis(approved=abs(int(attrs['approved'].encode('utf-8'))),
#                approved_by=self.utEmptyToNone(attrs['approved_by'].encode('utf-8')))
#            if attrs['releasedate'].encode('utf-8') != '':
#                ob.setReleaseDate(attrs['releasedate'].encode('utf-8'))
#            ob.submitThis()
#            ob.import_comments(discussion)
#            self.recatalogNyObject(ob)

class NyReportReference(NyAttributes, reportreference_item, NyContainer, NyCheckControl):
    """ """

    meta_type = METATYPE_OBJECT
    meta_label = LABEL_OBJECT
    icon = 'misc_/NaayaContent/NyReportReference.gif'
    icon_marked = 'misc_/NaayaContent/NyReportReference_marked.gif'

    def manage_options(self):
        """ """
        l_options = ()
        if not self.hasVersion():
            l_options += ({'label': 'Properties', 'action': 'manage_edit_html'},)
        l_options += ({'label': 'View', 'action': 'index_html'},) + NyContainer.manage_options[3:8]
        return l_options

    meta_types = ()
    all_meta_types = meta_types

    security = ClassSecurityInfo()

    def __init__(self, id, title, description, coverage, keywords, sortorder, contributor, releasedate, lang, reference, ref_links):
        """ """
        self.id = id
        reportreference_item.__dict__['__init__'](self,title, description, coverage, keywords, sortorder, releasedate, lang, reference, ref_links)
        NyCheckControl.__dict__['__init__'](self)
        NyContainer.__dict__['__init__'](self)
        self.contributor = contributor

    def __getattr__(self, name):
        """
        Called when an attribute lookup has not found the attribute in the usual places.
        @param name: the attribute name
        @return: should return the attribute value or raise an I{AttributeError} exception.
        """
        if name.startswith('objectkeywords_'):
            parts = name.split('_')
            func, lang = parts[0], parts[1]
            return self.objectkeywords(lang)
        elif name.startswith('istranslated_'):
            parts = name.split('_')
            func, lang = parts[0], parts[1]
            return self.istranslated(lang)
        raise AttributeError, name

    security.declarePrivate('objectkeywords')
    def objectkeywords(self, lang):
        return u' '.join([self._objectkeywords(lang)])

    security.declarePrivate('syndicateThis')
    def syndicateThis(self, lang=None):
        pass

    #zmi actions
    security.declareProtected(view_management_screens, 'manageProperties')
    def manageProperties(self, title='', description='', coverage='', keywords='',
        sortorder='', approved='', releasedate='', discussion='', lang='', reference='', REQUEST=None, **kwargs):
        """ """
        if not self.checkPermissionEditObject():
            raise EXCEPTION_NOTAUTHORIZED, EXCEPTION_NOTAUTHORIZED_MSG
        try: sortorder = abs(int(sortorder))
        except: sortorder = DEFAULT_SORTORDER
        if approved: approved = 1
        else: approved = 0
        releasedate = self.process_releasedate(releasedate)
        if not lang: lang = self.gl_get_selected_language()

        if self.getLocalProperty('reference', 'en'):
            title = self.getLocalProperty('reference', 'en')
        else:
            title = reference

        self.save_properties(title, description, coverage, keywords, sortorder, releasedate, lang, reference)
        ref_links = {'en':[]}
        if lang == 'en':
            ref_links['en'].extend(self.getReferenceData(reference))
            self.save_references(ref_links)
        self.updatePropertiesFromGlossary(lang)
        self.updateDynamicProperties(self.processDynamicProperties(METATYPE_OBJECT, REQUEST, kwargs), lang)
        if approved != self.approved:
            if approved == 0: approved_by = None
            else: approved_by = self.REQUEST.AUTHENTICATED_USER.getUserName()
            self.approveThis(approved, approved_by)
        self._p_changed = 1
        if discussion: self.open_for_comments()
        else: self.close_for_comments()
        self.recatalogNyObject(self)
        if REQUEST: REQUEST.RESPONSE.redirect('manage_edit_html?save=ok&lang=%s' % lang)

    #site actions
    security.declareProtected(PERMISSION_EDIT_OBJECTS, 'commitVersion')
    def commitVersion(self, REQUEST=None):
        """ """
        if (not self.checkPermissionEditObject()) or (self.checkout_user != self.REQUEST.AUTHENTICATED_USER.getUserName()):
            raise EXCEPTION_NOTAUTHORIZED, EXCEPTION_NOTAUTHORIZED_MSG
        if not self.hasVersion():
            raise EXCEPTION_NOVERSION, EXCEPTION_NOVERSION_MSG
        self._local_properties_metadata = deepcopy(self.version._local_properties_metadata)
        self._local_properties = deepcopy(self.version._local_properties)
        self.sortorder =    self.version.sortorder
        self.releasedate =  self.version.releasedate
        self.setProperties(deepcopy(self.version.getProperties()))
        self.checkout = 0
        self.checkout_user = None
        self.version = None
        self._p_changed = 1
        self.recatalogNyObject(self)
        if REQUEST: REQUEST.RESPONSE.redirect('%s/index_html' % self.absolute_url())

    security.declareProtected(PERMISSION_EDIT_OBJECTS, 'startVersion')
    def startVersion(self, REQUEST=None):
        """ """
        if not self.checkPermissionEditObject():
            raise EXCEPTION_NOTAUTHORIZED, EXCEPTION_NOTAUTHORIZED_MSG
        if self.hasVersion():
            raise EXCEPTION_STARTEDVERSION, EXCEPTION_STARTEDVERSION_MSG
        self.checkout = 1
        self.checkout_user = self.REQUEST.AUTHENTICATED_USER.getUserName()
        self.version = reportreference_item(self.title, self.description, self.coverage,
            self.keywords, self.sortorder, self.releasedate, self.gl_get_selected_language())
        self.version._local_properties_metadata = deepcopy(self._local_properties_metadata)
        self.version._local_properties = deepcopy(self._local_properties)
        self.version.setProperties(deepcopy(self.getProperties()))
        self._p_changed = 1
        self.recatalogNyObject(self)
        if REQUEST: REQUEST.RESPONSE.redirect('%s/edit_html' % self.absolute_url())

    security.declareProtected(PERMISSION_EDIT_OBJECTS, 'saveProperties')
    def saveProperties(self, title='', description='', coverage='', keywords='',
        sortorder='', releasedate='', discussion='', lang=None, reference='', REQUEST=None, **kwargs):
        """ """
        if not self.checkPermissionEditObject():
            raise EXCEPTION_NOTAUTHORIZED, EXCEPTION_NOTAUTHORIZED_MSG
        if not sortorder: sortorder = DEFAULT_SORTORDER
        if lang is None: lang = self.gl_get_selected_language()
        #check mandatory fiels
        r = self.getSite().check_pluggable_item_properties(METATYPE_OBJECT, title=title, \
            description=description, coverage=coverage, keywords=keywords, sortorder=sortorder, \
            releasedate=releasedate, discussion=discussion, reference=reference)
        if not len(r):
            sortorder = int(sortorder)
            if not self.hasVersion():
                #this object has not been checked out; save changes directly into the object
                releasedate = self.process_releasedate(releasedate, self.releasedate)
                self.save_properties(title, description, coverage, keywords, sortorder,
                    releasedate, lang, reference)
                self.updatePropertiesFromGlossary(lang)
                self.updateDynamicProperties(self.processDynamicProperties(METATYPE_OBJECT, REQUEST, kwargs), lang)
            else:
                #this object has been checked out; save changes into the version object
                if self.checkout_user != self.REQUEST.AUTHENTICATED_USER.getUserName():
                    raise EXCEPTION_NOTAUTHORIZED, EXCEPTION_NOTAUTHORIZED_MSG
                releasedate = self.process_releasedate(releasedate, self.version.releasedate)
                self.version.save_properties(title, description, coverage, keywords, sortorder, releasedate, lang, reference)
                self.version.updatePropertiesFromGlossary(lang)
                self.version.updateDynamicProperties(self.processDynamicProperties(METATYPE_OBJECT, REQUEST, kwargs), lang)
            if discussion: self.open_for_comments()
            else: self.close_for_comments()
            self._p_changed = 1
            self.recatalogNyObject(self)
            if REQUEST:
                self.setSessionInfo([MESSAGE_SAVEDCHANGES % self.utGetTodayDate()])
                REQUEST.RESPONSE.redirect('%s/edit_html?lang=%s' % (self.absolute_url(), lang))
        else:
            if REQUEST is not None:
                self.setSessionErrors(r)
                self.set_pluggable_item_session(METATYPE_OBJECT, id=id, title=title, \
                    description=description, coverage=coverage, keywords=keywords, \
                    sortorder=sortorder, releasedate=releasedate, discussion=discussion, reference=reference)
                REQUEST.RESPONSE.redirect('%s/edit_html?lang=%s' % (self.absolute_url(), lang))
            else:
                raise Exception, '%s' % ', '.join(r)

    #zmi pages
    security.declareProtected(view_management_screens, 'manage_edit_html')
    manage_edit_html = PageTemplateFile('zpt/reportreference_manage_edit', globals())

    #site pages
    security.declareProtected(PERMISSION_ADD_OBJECT, 'add_html')
    def add_html(self, REQUEST=None, RESPONSE=None):
        """ """
        return self.getFormsTool().getContent({'here': self}, 'reportreference_add')

    security.declareProtected(view, 'index_html')
    def index_html(self, REQUEST=None, RESPONSE=None):
        """ """
        return self.getFormsTool().getContent({'here': self}, 'reportreference_index')

    security.declareProtected(PERMISSION_EDIT_OBJECTS, 'edit_html')
    def edit_html(self, REQUEST=None, RESPONSE=None):
        """ """
        return self.getFormsTool().getContent({'here': self}, 'reportreference_edit')

    security.declareProtected(PERMISSION_DELETE_OBJECTS, 'deleteObjects')
    def deleteObjects(self, REQUEST=None):
        """ """
        id_list = self.utConvertToList(REQUEST.get('id', []))
        try: self.manage_delObjects(id_list)
        except: self.setSessionErrors(['Error while delete data.'])
        else: self.setSessionInfo(['Item(s) deleted.'])
        if REQUEST: REQUEST.RESPONSE.redirect('index_html')

    security.declareProtected(view, 'report_macro_objecttree_html')
    def report_macro_objecttree_html(self, REQUEST=None, RESPONSE=None):
        """ """
        return self.getFormsTool().getForm('report_macro_objecttree')

InitializeClass(NyReportReference)

manage_addNyReportReference_html = PageTemplateFile('zpt/reportreference_manage_add', globals())
manage_addNyReportReference_html.kind = METATYPE_OBJECT
manage_addNyReportReference_html.action = 'addNyReportReference'

config.update({
    'constructors': (manage_addNyReportReference_html, addNyReportReference),
    'folder_constructors': [
            # NyFolder.manage_addNyReportReference_html = manage_addNyReportReference_html
            ('manage_addNyReportReference_html', manage_addNyReportReference_html),
            ('reportreference_add_html', reportreference_add_html),
            ('addNyReportReference', addNyReportReference),
            (config['import_string'], importNyReportReference),
        ],
    'add_method': addNyReportReference,
    'validation': issubclass(NyReportReference, NyValidation),
    '_class': NyReportReference,
})

def get_config():
    return config
